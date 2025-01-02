"""This module contains the ``SeleniumMiddleware`` scrapy middleware"""
"""
Author : Nauman Khan Gori
date : 31/10/2023
purpose : This module contains the ``SeleniumMiddleware`` scrapy middleware
"""
from importlib import import_module
# from selenium.webdriver.support.ui import WebDriverWait
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
import logging
from .http import SeleniumRequest
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService

class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, driver_executable_path, driver_arguments,
        browser_executable_path):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        """

        webdriver_base_path = f'selenium.webdriver.{driver_name}'

        driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        driver_klass = getattr(driver_klass_module, 'WebDriver')

        driver_options_module = import_module(f'{webdriver_base_path}.options')
        driver_options_klass = getattr(driver_options_module, 'Options')

        driver_options = driver_options_klass()
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        driver_kwargs = {
            'executable_path': driver_executable_path,
            f'{driver_name}_options': driver_options
        }
            # selenium4+ & webdriver-manager
        try:
            if driver_name and driver_name.lower() == 'chrome':
                # options = webdriver.ChromeOptions()
                # options.add_argument(o)
                self.driver = webdriver.Chrome(options=driver_options,
                                                service=ChromeService(ChromeDriverManager().install()))
            elif driver_name and driver_name.lower()=='firefox':
                self.driver = webdriver.Firefox(service=GeckoDriverManager().install(),options=driver_options)
        except:
            raise NotConfigured(
                'DRIVER RENDERING ERROR'
            )



    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        driver_executable_path = crawler.settings.get("SELENIUM_DRIVER_EXECUTABLE_PATH")
        browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        middleware = cls(
            driver_name=driver_name,
            driver_executable_path=driver_executable_path,
            driver_arguments=driver_arguments,
            browser_executable_path=browser_executable_path
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None
        self.driver.get(request.url)
        for cookie_name, cookie_value in request.cookies.items():
            self.driver.add_cookie(
                {
                    'name': cookie_name,
                    'value': cookie_value
                }
            )
        if request.wait_until:
            WebDriverWait(self.driver, request.wait_time).until(
                request.wait_until
            )

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)
        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""

        self.driver.quit()
        
    # def remove_elements(self):
    #     """Remove unwanted elements from the page before processing."""
    #     try:
    #         WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    #         unwanted_elements = [
    #             'app-sidebar-galaxy','nav', 'footer', 'header', 'aside','script', 'style', 'noscript', 'svg', '[role="alert"]', 
    #             '[role="banner"]', '[role="dialog"]', '[role="alertdialog"]',
    #             '[role="region"][aria-label*="skip" i]', '[aria-modal="true"]','[class="folder"]'
    #         ]
    #         script = "var elements = document.querySelectorAll(arguments[0]);" \
    #                  "elements.forEach(function(el) { el.parentNode.removeChild(el);  });"
    #         for selector in unwanted_elements:
    #             self.driver.execute_script(script, selector)
    #     except TimeoutException:
    #         logging.warning('Timeout while waiting for elements to be available.')

