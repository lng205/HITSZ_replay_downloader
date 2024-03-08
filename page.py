import requests, re, subprocess, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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
    replays = get_replays(session, courses[course])

    if not os.path.exists(course):
        os.mkdir(course)

    for time, url in select_replays(replays).items():
        time = time.replace(":", "_").replace(" ", "_").replace("-", "_")
        hls_url = get_hls_url(url, session)

        output_file = os.path.join(course, f"{time}.mp4")

        command = [
            "ffmpeg",
            "-i",
            hls_url,
            "-c",
            "copy",  # Copy streams to avoid re-encoding
            "-bsf:a",
            "aac_adtstoasc",  # Fix for some HLS streams with AAC audio
            output_file,
        ]
        subprocess.run(command)


def select_courses(courses: dict):
    for index, course in enumerate(list(courses.keys())):
        print(f"{index + 1}. {course}")
    print("\n0. 选择其他学期")
    return int(input("请选择课程序号："))


def select_term(terms: dict) -> str:
    for index, term in enumerate(list(terms.keys())):
        print(f"{index + 1}. {term}")
    return int(input("请选择学期序号："))


def select_replays(replays: dict) -> dict[str, str]:
    for index, replay in enumerate(replays):
        print(f"{index + 1}. {replay}")

    range_input = input("请选择回放序号（示例：3-7,9）：")
    ranges = []
    for part in range_input.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            ranges.extend(list(range(start, end + 1)))
        else:
            ranges.append(int(part))
    times = list(replays.keys())
    return {times[index - 1]: replays[times[index - 1]] for index in ranges}


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


def get_replays(session: requests.Session, url: str) -> dict[str, str]:
    page = session.get(url, verify=False)
    soup = BeautifulSoup(page.text, "lxml")
    page_element = soup.find_all("span", class_="bkd")
    if not page_element:
        return extract_replays(page.text)
    total_page = int(re.search(r"共(\d+)页", page_element[1].text).group(1))
    replays = extract_replays(page.text)
    for i in range(2, total_page + 1):
        page = session.get(url + f"&page={i}", verify=False)
        replays.update(extract_replays(page.text))
    return replays


def extract_replays(page: str) -> dict[str, str]:
    soup = BeautifulSoup(page, "lxml")
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
