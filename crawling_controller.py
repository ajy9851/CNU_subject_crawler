import sys
import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from crawler.crawler_def import crawl_timetable, is_there_have_subject

def main():
    while True:
        options = Options()
        # 창 없이 실행
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--headless")
        options.capabilities["browserName"] = "chrome"
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(15)
        # #명령어 들어올 때까지 기다림
        # line = sys.stdin.readline()
        # if not line:
        #     break  # 명령어가 없으면 중단
        #
        # #명령어 json 디코딩
        # cmd = json.loads(line)

        cmd = {
            "cmd": "plan",
            "grade": "1",
            "term": "1",
            "subject_name": "수학1",
            "subject_code": "CLT0082-11",
        }

        # 명령어 처리
        if cmd["cmd"] == "plan":
            # result 초기화
            result = {}
            isTrue = {}

            # 사용자가 입력한 과목을 db에 저장 전 실제로 존재하는 과목인지 확인
            isTrue_result, isTrue_message = is_there_have_subject(driver, "1", "1", cmd["subject_name"], cmd["subject_code"])
            isTrue['result'] = isTrue_result
            isTrue['message'] = isTrue_message
            print(isTrue)


            # 호텔/비행기 찾고 관광지 찾아서 각각 result의 속성에 추가
            try:
                result.update(
                    crawl_timetable(driver, cmd["grade"], cmd["term"], cmd["subject_name"], cmd["subject_code"]))
                result["success"] = True
            except:
                result["success"] = False

            # result to JSON and print
            print(json.dumps(result, ensure_ascii=False))

            driver.quit()

            time.sleep(1)
            # flush
            sys.stdout.flush()


main()