import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import subprocess


BASE_URL = "https://sso.hitsz.edu.cn:7002/cas/login"
SERVICE_URL = "http://219.223.238.14:88/ve/"


def main():
    login = Login(input("请输入用户名："), input("请输入密码："))
    session = login.session

    courses = extract_courses(login.course_index.text)
    while True:
        course_select_index = select_courses(courses)
        if course_select_index == 0:
            terms = extract_terms(login.course_index.text)
            term = list(terms.keys())[select_term(terms) - 1]
            course_index_page = session.get(terms[term], verify=False)

            courses = extract_courses(course_index_page.text)
        else:
            break

    course = list(courses.keys())[course_select_index - 1]
    replays = extract_replays(session.get(courses[course], verify=False).text)

    for time, url in select_replays(replays).items():
        hls_url = get_hls_url(url, session)
        # print(f"Course: {course}, Time: {time}, URL: {hls_url}")
        command = [
            "ffmpeg",
            "-i",
            hls_url,  # Input file specification
            "-c",
            "copy",  # Copy streams to avoid re-encoding
            "-bsf:a",
            "aac_adtstoasc",  # Fix for some HLS streams with AAC audio
            "test.mp4",  # Output file
        ]
        subprocess.run(command)


def select_courses(courses: dict):
    for index, course in enumerate(list(courses.keys())):
        print(f"{index + 1}. {course}")
    print("\n0. 选择其他学期")
    return int(input("请输入你要选择的课程的序号："))


def select_term(terms: dict) -> str:
    for index, term in enumerate(list(terms.keys())):
        print(f"{index + 1}. {term}")
    return int(input("请输入你要选择的学期的序号："))


def select_replays(replays: dict) -> dict[str, str]:
    # TODO
    for index, replay in enumerate(replays):
        print(f"{index + 1}. {replay}")
    urls = {}
    while True:
        index = int(input("请输入你要选择的回放的序号："))
        if index == 0:
            break
        time = list(replays.keys())[index - 1]
        urls[time] = replays[time]
    return urls


def extract_terms(page: str) -> dict[str, str]:
    soup = BeautifulSoup(page, "lxml")
    content = soup.find("ul", class_="zxueId")
    elements = content.find_all("li")
    return {
        element.text: SERVICE_URL
        + "back/rp/common/rpIndex.shtml?method=studyCourseIndex&xq_code="
        + element["value"]
        for element in elements
    }


def extract_courses(page: str) -> dict[str, str]:
    soup = BeautifulSoup(page, "lxml")
    content = soup.find("div", class_="xue-content-left")
    courses = content.select("div.course-content > a")
    return {
        course.find("div", class_="course-num").contents[0].strip(): course.get("href")
        for course in courses
    }


def extract_replays(page: str) -> dict[str, str]:
    soup = BeautifulSoup(page, "lxml")
    total_page_element = soup.find_all("span", class_="bkd")[1]
    total_page = int(re.search(r"共(\d+)页", total_page_element.text).group(1))

    # TODO

    replays = {}
    content = soup.find("div", class_="curr-contlist")
    elements = content.select("ul > a")
    for element in elements:
        time = element.find("li", class_="titlem").contents[0].strip()
        onclick = element.get("onclick")
        match = re.search(
            r"getStuControlType\('([^']*)','([^']*)','([^']*)','([^']*)'\)", onclick
        )
        rpId, courseId, courseNum, fzId = match.groups()
        url = (
            SERVICE_URL
            + "back/rp/common/rpIndex.shtml?method=studyCourseDeatil&courseId="
            + courseId
            + "&dataSource=1&courseNum="
            + courseNum
            + "&fzId="
            + fzId
            + "&rpId="
            + rpId
            + "&publicRpType="
            + "1"
        )
        replays[time] = url
    return replays


def get_hls_url(url, session: requests.Session):
    page = session.get(url, verify=False)
    soup = BeautifulSoup(page.text, "lxml")
    scripts = soup.find_all("script", type="text/javascript")

    # The script tag containing the teaStreamHlsUrl is the last one
    script = scripts[-1]
    match = re.search(r'var teaStreamHlsUrl = "(.*?)";', script.text)
    teaStreamHlsUrl = match.group(1)

    playlist = session.get(teaStreamHlsUrl, verify=False)
    # The 3rd line in the playlist is the chuncklist name
    playlist = playlist.text.split("\n")[3]
    return urljoin(teaStreamHlsUrl, playlist)


class Login:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._login()

    def _get_login_page(self) -> requests.Response:
        return self.session.get(BASE_URL, params={"service": SERVICE_URL}, verify=False)

    def _get_lt(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "lxml")
        input_element = soup.find("input", attrs={"name": "lt"})
        return input_element.get("value")

    def _login_post(self, jsessionid: str, lt_value: str) -> requests.Response:
        data = {
            "username": self.username,
            "password": self.password,
            "rememberMe": "on",
            "lt": lt_value,
            "execution": "e1s1",
            "_eventId": "submit",
            "vc_username": "",
            "vc_password": "",
        }
        return self.session.post(
            f"{BASE_URL};jsessionid={jsessionid}",
            params={"service": SERVICE_URL},
            data=data,
            verify=False,
        )

    def _login(self):
        login_page = self._get_login_page()
        self.jsessionid = login_page.cookies.get("JSESSIONID")
        lt = self._get_lt(login_page.text)
        self.course_index = self._login_post(self.jsessionid, lt)


if __name__ == "__main__":
    main()
