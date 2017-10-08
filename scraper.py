'''
Usage:
    scraper.py <output_file> [options]

Options:
    --help                              show this screen
    --unit_of_application=<unit>        the unit of application to scrape
    --specialty=<specialty>             the specialty to search on
    --avoid_specialty=<avoid_spec>      the specialties (comma-separated) to
                                        filter out
'''
import csv
import traceback
from docopt import docopt
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from constants import (
    CHROME_BINARY_LOCATION, ORIGINAL_REQUEST, BASE_FOUNDATION_PAGE,
    STATIC_OUTPUT_FIELDNAMES, UNIT_OF_APPLICATION_KEY, PROGRAM_TYPE_KEY,
    PROGRAM_TITLE_KEY, DEANERY_KEY, FOUNDATION_SCHOOL_KEY, EMPLOYER_KEY,
    SEMESTER_YEAR_KEY, SEMESTER_SITE_KEY, SEMESTER_LOCATION_KEY,
    SEMESTER_SPECIALTY_KEY, SEMESTER_DESCRIPTION_KEY, NUMBER_SEMESTERS,
    PROGRAM_ID_KEY, PROGRAM_DESCRIPTION_KEY, DURATION_KEY
)
from xpath import (
    POST_LOGIN_ELEMENT, RESULT_BOX_ELEMENT, RESULT_DETAILS_BUTTON,
    RESULT_DETAILS_ELEMENT, RESULT_ID, RESULT_TYPE, RESULT_TITLE,
    RESULT_UNIT, RESULT_DEANERY, RESULT_SCHOOL, RESULT_DURATION,
    RESULT_EMPLOYER, MODAL_CLOSE_BUTTON, NEXT_PAGE_LINK, SEMESTER_ROW_PARSING,
    UNIT_OF_APPLICATION_SELECT, SEARCH_BUTTON
)


class NoSuchSearchOption(Exception):
    pass


class ProgrammeResult(dict):
    def __init__(self, listing_element, details_element, fieldnames):
        self._parse(listing_element, details_element)
        self.fieldnames = fieldnames

    def get_xpath_text(self, elem, xpath):
        return elem.find_element(By.XPATH, xpath).text

    def set(self, key, value):
        self.__setitem__(key, value)

    def _parse(self, elem, d_elem):
        self.set(PROGRAM_ID_KEY, self.get_xpath_text(elem, RESULT_ID))
        self.set(PROGRAM_TYPE_KEY, self.get_xpath_text(d_elem, RESULT_TYPE))
        self.set(PROGRAM_TITLE_KEY, self.get_xpath_text(d_elem, RESULT_TITLE))
        self.set(UNIT_OF_APPLICATION_KEY, self.get_xpath_text(
            d_elem, RESULT_UNIT
        ))
        self.set(DEANERY_KEY, self.get_xpath_text(elem, RESULT_DEANERY))
        self.set(FOUNDATION_SCHOOL_KEY, self.get_xpath_text(
            d_elem, RESULT_SCHOOL
        ))
        self.set(DURATION_KEY, self.get_xpath_text(d_elem, RESULT_DURATION))
        self.set(EMPLOYER_KEY, self.get_xpath_text(elem, RESULT_EMPLOYER))
        self.set(PROGRAM_DESCRIPTION_KEY, self.get_xpath_text(
            d_elem, RESULT_DURATION
        ))

        for idx, row in enumerate(
            d_elem.find_elements(By.XPATH, SEMESTER_ROW_PARSING)
        ):
            cell_text = [td.text for td in row.find_elements(By.XPATH, './td')]
            self.set(SEMESTER_YEAR_KEY.format(idx + 1), cell_text[0])
            self.set(SEMESTER_SITE_KEY.format(idx + 1), cell_text[1])
            self.set(SEMESTER_LOCATION_KEY.format(idx + 1), cell_text[2])
            self.set(SEMESTER_SPECIALTY_KEY.format(idx + 1), cell_text[3])
            self.set(SEMESTER_DESCRIPTION_KEY.format(idx + 1), cell_text[4])

    def does_pass_filter(self, filter_options):
        for filter_key, filter_value in filter_options.iteritems():
            if filter_value is None:
                continue
            result_value = self.__getitem__(filter_key)

            if result_value is not None:
                continue

            if result_value.lower() != filter_value.lower():
                print('Filtered placement due to {}'.format(filter_key))
                return False

        specialties = [
            self.__getitem__(SEMESTER_SPECIALTY_KEY.format(x), None)
            for x in range(1, NUMBER_SEMESTERS + 1)
        ]

        avoid_specialties = filter_options['avoid_specialty']
        for a_spec in avoid_specialties:
            for spec in specialties:
                if a_spec.lower() == spec.lower():
                    print('Filtered placement due to {} specialty'.format(
                        a_spec
                    ))
                    return False

        return True


class OutputWriter(object):
    def __init__(self, filename, fieldnames):
        self.file = open(filename, 'w')
        self.writer = csv.DictWriter(
            self.file, fieldnames=fieldnames, extrasaction='ignore'
        )
        self.writer.writeheader()

    def write_result(self, result):
        self.writer.writerow(result)

    def cleanup(self):
        self.file.close()


class Scraper(object):
    def __init__(self, filter_options):
        options = webdriver.ChromeOptions()
        options.binary_location = CHROME_BINARY_LOCATION
        options.add_argument('window-size=800x841')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.filter_options = filter_options

    def login(self):
        self.driver.get(ORIGINAL_REQUEST)
        print("Waiting for user to sign in.")

        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, POST_LOGIN_ELEMENT))
            )
        except TimeoutException:
            print("Waited too long for user. Cancelling login.")
            return False

        return True

    def get_results(self, fieldnames):
        next_page_link = self.driver.find_element(By.XPATH, NEXT_PAGE_LINK)

        while next_page_link.get_attribute('disabled') is None:
            listed_results = self.driver.find_elements(
                By.XPATH, RESULT_BOX_ELEMENT
            )

            for elem in listed_results:
                elem.find_element(By.XPATH, RESULT_DETAILS_BUTTON).click()
                details_element = self.driver.find_element(
                    By.XPATH, RESULT_DETAILS_ELEMENT
                )
                yield ProgrammeResult(elem, details_element, fieldnames)

                # deactivate modal click
                elem.find_element(By.XPATH, MODAL_CLOSE_BUTTON).click()

            next_page_link.click()
            next_page_link = self.driver.find_element(By.XPATH, NEXT_PAGE_LINK)

    def _get_all_options(self, select_elem):
        options = select_elem.find_elements(By.XPATH, './/option')
        return [x.get_attribute('value') for x in options]

    def _select_unit_of_application(self, unit_of_application):
        elem = self.driver.find_element(By.XPATH, UNIT_OF_APPLICATION_SELECT)
        units = self._get_all_options(elem)
        if unit_of_application not in units:
            raise NoSuchSearchOption(
                "No Unit of Application found for".format(unit_of_application)
            )
        select = Select(elem)
        select.select_by_value(unit_of_application)

    def resolve_search_filters(self, filters):
        search_necessary = False

        if UNIT_OF_APPLICATION_KEY in filters:
            self._select_unit_of_application(filters[UNIT_OF_APPLICATION_KEY])
            search_necessary = True

        if search_necessary:
            self.driver.find_element(By.XPATH, SEARCH_BUTTON).click()

    def scrape_data(self, output, fieldnames):
        discovered = set()

        for result in self.get_results(fieldnames):
            if result[PROGRAM_ID_KEY] in discovered:
                print("Found duplicate for id: {}".format(
                    result[PROGRAM_ID_KEY]
                ))
                continue

            if len(discovered) and len(discovered) % 100 == 0:
                print("Discovered {} results so far".format(len(discovered)))

            output.write_result(result)

    def cleanup(self):
        self.driver.quit()


if __name__ == '__main__':
    args = docopt(__doc__)

    filter_specialties = args['--avoid_specialty']
    if filter_specialties:
        filter_specialties = filter_specialties.split(',')

    filter_options = {
        UNIT_OF_APPLICATION_KEY: args['--unit_of_application'],
        'specialty': args['--specialty'],
        'avoid_specialty': filter_specialties
    }

    dynamic_fieldnames = []
    for x in range(1, NUMBER_SEMESTERS + 1):
        dynamic_fieldnames.append(SEMESTER_YEAR_KEY.format(x))
        dynamic_fieldnames.append(SEMESTER_SITE_KEY.format(x))
        dynamic_fieldnames.append(SEMESTER_LOCATION_KEY.format(x))
        dynamic_fieldnames.append(SEMESTER_SPECIALTY_KEY.format(x))
        dynamic_fieldnames.append(SEMESTER_DESCRIPTION_KEY.format(x))
    fieldnames = STATIC_OUTPUT_FIELDNAMES + dynamic_fieldnames

    scraper = Scraper(filter_options)
    output_writer = OutputWriter(args['<output_file>'], fieldnames)
    try:
        login_result = scraper.login()

        if login_result:
            scraper.driver.get(BASE_FOUNDATION_PAGE)
            scraper.resolve_search_filters(filter_options)
            scraper.scrape_data(output_writer, fieldnames)
        else:
            print("Failed to log in")
    except Exception as e:
        scraper.driver.save_screenshot("exception.png")
        print(traceback.format_exc())
        raise e
    finally:
        scraper.cleanup()
        output_writer.cleanup()
