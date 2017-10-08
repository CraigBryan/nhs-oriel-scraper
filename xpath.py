POST_LOGIN_ELEMENT = '//li[@id="dashboard"]'
RESULT_BOX_ELEMENT = (
    '//div[@class="data-content"]//div[@class="ListPage"]/div'
    '[contains(@class, "row")]'
)
RESULT_DETAILS_BUTTON = (
    './/div[contains(@class, "button-container")]/a[@title="View Details"]'
)
RESULT_DETAILS_ELEMENT = (
    '//div[@id="hicomCommonModalBody"]//div[@id="printform"]'
)
MODAL_CLOSE_BUTTON = '//span[@id="hicomCommonModalClose"]'
NEXT_PAGE_LINK = (
    '//ul[contains(@class, "pagination_button")]//a[contains(text(), "Next")]'
)
UNIT_OF_APPLICATION_SELECT = '//select[@id="UnitOfApplication"]'
SEARCH_BUTTON = '//input[@id="btnSearch"]'

# result parsing
RESULT_ID = './/h6'
RESULT_TYPE = './/td[contains(text(), "Programme Type")]/following-sibling::td'
RESULT_TITLE = (
    './/td[contains(text(), "Programme Title")]/following-sibling::td'
)
RESULT_UNIT = (
    './/td[contains(text(), "Unit of Application")]/following-sibling::td'
)
RESULT_DEANERY = (
    './/div[contains(p/text(), "Deanery")]/following-sibling::div/p'
)
RESULT_SCHOOL = (
    './/td[contains(text(), "Foundation School")]/following-sibling::td'
)
RESULT_DURATION = (
    './/td[contains(text(), "Programme duration")]/following-sibling::td'
)
RESULT_EMPLOYER = (
    './/div[contains(p/text(), "Employer")]/following-sibling::div/p'
)
SEMESTER_ROW_PARSING = './/table[contains(@class, "placement")]/tbody//tr'
