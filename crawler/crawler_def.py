from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import re
# from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time

# 검색 결과가 없을 때 메시지를 출력하는 함수
# def check_no_results(driver):
#     try:
#         # '시간표 검색결과가 없습니다' 메시지가 있는지 확인
#         driver.find_element(By.XPATH, "//td[text()='시간표 검색결과가 없습니다']")
#         # 메시지가 있으면 True 반환
#         return True
#     except NoSuchElementException:
#         # 메시지가 없으면 False 반환
#         return False

#function - 문자열에 들어간 공백, 개행, 탭 없애기
def delete_whitespace(string):
    return re.sub(r'\s+', '', string) # \s : whitespace, sub() : 찾은걸 두 번째 인자로 대체하고 반환

def clean_subject_name(subject_name):
    # 괄호와 괄호 안의 내용 제거
    return re.sub(r'\(.*?\)', '', subject_name).strip()

def is_there_have_subject(driver, grade, term, subject_name, subject_code):
    try:
        # 과목명 정제
        cleaned_subject_name = clean_subject_name(subject_name)

        # 과목 코드와 분반 번호 분리 및 확인
        subject_code_parts = subject_code.split('-')
        subject_code_only = delete_whitespace(subject_code_parts[0])
        if len(subject_code_parts) < 2:
            return False, "분반 입력이 잘못되었습니다."

        #section_number = delete_whitespace(subject_code_parts[1])

        # 해당 과목이 있는지 검색
        driver.get("https://hakstd.jnu.ac.kr/web/Suup/TimeTable/Suup053C.aspx")

        # 학년, 학기, 교과목명 입력
        Select(driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_ddlGrade")).select_by_value(str(grade))
        Select(driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_ddlTerm")).select_by_value(str(term))
        driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_txtSubj").send_keys(cleaned_subject_name)

        # 검색 버튼 클릭
        driver.find_element(By.CSS_SELECTOR, "#ContentPlaceHolder_ContentPlaceHolderSub_ibtnSearch").click()
        time.sleep(0.5)  # 페이지 로딩 대기

        # 과목 코드에 해당하는 행 찾기
        rows = driver.find_elements(By.XPATH, "//table[@id='ContentPlaceHolder_ContentPlaceHolderSub_gvData']/tbody/tr")
        for row in rows:
            # 과목 코드와 분반 번호를 함께 추출
            course_code_and_section = delete_whitespace(row.find_element(By.XPATH, ".//td[contains(@data-th, '교과목번호')]").text)

            # 과목 코드와 분반 번호를 분리하여 비교
            if course_code_and_section == subject_code:
                # 해당 과목 코드가 있으면 True 반환
                return True, course_code_and_section

        # 해당 과목 코드를 찾지 못한 경우 False 반환
        return False, "과목이 존재하지 않습니다."

    except NoSuchElementException:
        # 요소를 찾지 못한 경우
        return False, "과목이 존재하지 않습니다."





# 정상적으로 시간표가 검색되었을 때 크롤링을 진행하는 함수
def crawl_timetable(driver, grade, term, subject_name, subject_code):
    driver.get("https://hakstd.jnu.ac.kr/web/Suup/TimeTable/Suup053C.aspx")

    # 학년, 학기, 교과목명, 교수명 입력
    Select(driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_ddlGrade")).select_by_value(grade)
    Select(driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_ddlTerm")).select_by_value(term)
    driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolderSub_txtSubj").send_keys(subject_name)

    # 검색 버튼 클릭
    driver.find_element(By.CSS_SELECTOR, "#ContentPlaceHolder_ContentPlaceHolderSub_ibtnSearch").click()
    time.sleep(0.5)  # 페이지 로딩 대기

    # 과목 코드와 분반 번호 분리
    subject_code_parts = subject_code.split('-')
    subject_code_only = subject_code_parts[0].strip()
    section_number = subject_code_parts[1].strip() if len(subject_code_parts) > 1 else None

    # '시간표 검색결과가 없습니다' 메시지가 있는지 확인
    if driver.find_elements(By.XPATH, "//td[text()='시간표 검색결과가 없습니다']"):
        return {"success": False, "message": "시간표 검색결과가 없습니다."}

    results = {}


    # 과목 코드에 해당하는 행 찾기
    try:
        rows = driver.find_elements(By.XPATH, "//table[@id='ContentPlaceHolder_ContentPlaceHolderSub_gvData']/tbody/tr")
        for row in rows:
            # 과목 코드와 분반 번호를 함께 추출
            course_code_and_section = row.find_element(By.XPATH, ".//td[contains(@data-th, '교과목번호')]").text.strip()

            # 과목 코드와 분반 번호를 분리하여 비교
            course_code, section_number_in_row = course_code_and_section.split('-')
            course_code = course_code.strip()
            section_number_in_row = section_number_in_row.strip()

            print(course_code)
            print(section_number_in_row)
            if course_code == subject_code_only and (section_number is None or section_number == section_number_in_row):
                # 여석/공통기간여석/(자/타/부전) 데이터 추출 및 파싱
                seats_elements = row.find_elements(By.XPATH, ".//td[contains(@data-th, '여석/공통기간여석')]/p")
                # 학년여석 정보 추출 (파란색 텍스트)
                ja, ta, bujeon = seats_elements[0].text.strip().strip('()').split('/')
                # 공통기간여석 정보 추출 (빨간색 텍스트)
                common_ja, common_ta, common_bujeon = seats_elements[1].text.strip().strip('()').split('/')
                # 정보를 딕셔너리로 저장
                timetable_data = {
                    "year_seats": {
                        "ja": ja,
                        "ta": ta,
                        "bujeon": bujeon
                    },
                    "common_seats": {
                        "ja": common_ja,
                        "ta": common_ta,
                        "bujeon": common_bujeon
                    }
                }
                return {"success": True, "timetable_data": timetable_data}

        # for문을 빠져나왔지만 해당 과목 코드를 찾지 못한 경우
        return {"success": False, "message": "해당 과목 코드를 찾을 수 없습니다."}

    except NoSuchElementException:
        return {"success": False, "message": "시간표 정보를 추출하는 중 오류가 발생했습니다."}

