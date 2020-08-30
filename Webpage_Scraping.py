"""
This script scrapes the City GIS Map Gallery page for URLs and URL status and produces a csv of the results.

The 3rd party module selenium is used to open URLs and scrape details using Google Chrome and the WebDriver for Chrome.
The WebDriver for Chrome executable that matches the installed Chrome version needs to be separately downloaded
from the Chromium.org website and pointed to by the webdriver module object, but does not require installation.

Python version: 3.7
Author: Gavin Leavitt

"""

# 3rd party imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException
# Native imports
from datetime import date
import time
import csv

# start time of script
start_time = time.time()

# Not sure why this is needed, think this needs to exist but can be empty
opts = Options()
# opens browser in headless mode, no UI running in background
opts.headless = True
# Driver path, make sure driver matches version of browser, this driver is for chrome 83
driver_path = r'\chrome83\chromedriver_win32\chromedriver.exe'
# driver_path = r'B:\Python\Web_scraping\Chrome_Driver\chrome83\chromedriver_win32\chromedriver.exe'
# how long to wait until page load times out
waittime = 5
# Build driver, any major browser can be used, Chrome version 83 is used here, driver version must match browser
# install version
driver = webdriver.Chrome(options=opts, executable_path=driver_path)
# fields for which links will be tested, these values are used to add to the result dictionary as links are checked
link_values = ['REST_Link', 'AGOL_Link', 'Metadata_Link', 'WFS_Link', 'WMS_Link', 'Iframe_Webmap_Link']
# Common error messages that occur when links are wrong/broken, selenium can't check for HTTP status responses,
# so the web page contents need to be checked against using this values
error_msg = ["Please contact your system administrator.", "Unauthorized", "Not Found",
             "Item does not exist or is inaccessible.", "Error occurred while processing request", "Error occurred",
             "Please contact your system administrator."]
# Fields to be generated and populated in the output csv
csv_fields = ["gallery_entry_name", 'Gallery_Link', "REST_Link", "AGOL_Link", "Metadata_Link", "WFS_Link", "WMS_Link",
              "Iframe_Webmap_Link", "Iframe_Webmap_ID", "PDF_Link_Text", "PDF_Download_LINK", "PDF_File_Size",
              "REST_Link_Status", "AGOL_Link_Status", "Metadata_Link_Status", "WFS_Link_Status", "WMS_Link_Status",
              "Iframe_Webmap_Link_Status", "Summary Status"]
# current day for naming output file
currentday = date.today().strftime("%Y%m%d")
# output csv location
# output_csv = r'B:\Python\Web_scraping\scraping_results' + f"_{currentday}.csv"
output_csv = r'\scraping_results' + f"_{currentday}.csv"

# functions
def load_map_page(URL, waittime=waittime):
    """
    Uses selenium to load the map gallery entry page. Selenium will wait up to waittime seconds for the page to load.
    After page is loaded then the driver object is returned, this method is used because some pages may require more
    time for AJAX data to load, after the main page is loaded.

    :param URL: HTTPS URL of the map gallery entry to be loaded
    :return: Chrome Driver Object.
    """
    # Get the website
    driver.get(URL)
    # Wait up to waittime seconds for page to load, page is considered loaded when the link to the services directory
    # exists. This was chosen because this is the primary link of interest on the page
    try:
        WebDriverWait(driver, waittime).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Services Directory")))
        return driver
    except TimeoutException:
        # If element doesn't load by waittime, catch the TimeoutException and return the normal driver.get result,
        # even though the page and elements aren't properly loaded, try/except blocks further in the code will catch
        # the errors and handle them in the CSV output
        print("Timed out on page load")
        return driver


# Get total number of map gallery pages to review
def totalpages(URL):
    # get the web page from URL
    driver.get(URL)
    # Use the "last page" link at the bottom of the page to determine how many pages the map gallery contains
    # spaces in class name must be replaced by "." since this DOM element has two classes, "pager-last" and "last"
    last_page = str(
        driver.find_element_by_class_name('pager-last.last').find_element_by_tag_name("a").get_attribute('href'))
    # Grab the end of the link text that states the last page
    max_pg = last_page.split("=")[1]
    return max_pg


def gallery_links_visit(URL):
    """
    Builds a list of links to visit. Grabs all map gallery entries inside the input URL.
    :param URL: Map Gallery page to visit formatted as a HTTPS URL
    :return: List of formatted HTTPS URLs for each map gallery entry inside the provided URL
    """
    # get the web page from URL
    driver.get(URL)
    # All map gallery entries are contained within divs with the class name "brgt mcfw"
    # spaces in class name must be replaced by "." since this DOM element has two classes, "brgt" and "mcfw"
    linkcontainers = driver.find_elements_by_class_name('brgt.mcfw')
    links_visited = []
    # Loop over result object list(divs containing the map gallery entries)
    for item in linkcontainers:
        # Dig into the list objects to get the href link: get the link element with the link tag name
        # <a> then the href contents and extend the links visited list
        links_visited.extend([item.find_element_by_tag_name("a").get_attribute('href')])
    return links_visited


def galleryentries(links_to_visit):
    """
    Go through each map gallery entry URL gathering the GIS relevant URLs and add to dictionary. For each link selenium
    attempts to find the relevant link, if found it adds the link to the associated second level dictionary key, if
    a selenium exception is thrown because the element can't be found, then the key value is assigned "Error".

    This function doesn't check if the links are valid, only that they exist.

    :param links_to_visit: List of HTTPS URLs to visit
    :return: Dictionary: Two level dictionary with first level being service name and second level being URLs to GIS
        relevant locations
    """
    res = {}
    for webpage in links_to_visit:
        print(f"Working on webpage: {webpage}")
        # Split the service name from the URL
        shortname = webpage.split("/map/")[1]
        # use service name as key to first level dict
        res[shortname] = {}
        # get the web page from URL, using function to allow page load time
        driver = load_map_page(webpage)
        # Map Gallery entry URL
        res[shortname]['Gallery_Link'] = webpage
        # Populate dictionary with try/except blocks
        try:
            # rest = driver.find_element_by_partial_link_text("View ArcGIS REST Services Directory").get_attribute('href')
            # Allows for typos or dynamic link texts when searching for elements
            rest = driver.find_element_by_partial_link_text("Services Directory").get_attribute('href')
            res[shortname]['REST_Link'] = rest
        except NoSuchElementException:
            res[shortname]['REST_Link'] = "Error"
        try:
            agol = driver.find_element_by_partial_link_text("ArcGIS Online").get_attribute('href')
            res[shortname]['AGOL_Link'] = agol
        except NoSuchElementException:
            res[shortname]['AGOL_Link'] = "Error"
        try:
            metadata = driver.find_element_by_class_name("pane-node-field-map-meta-data").find_element_by_tag_name(
                "a").get_attribute('href')
            res[shortname]['Metadata_Link'] = metadata
        except NoSuchElementException:
            res[shortname]['Metadata_Link'] = "Error"
        try:
            WFS = driver.find_element_by_link_text("WFS").get_attribute('href')
            res[shortname]['WFS_Link'] = WFS
        except NoSuchElementException:
            res[shortname]['WFS_Link'] = "Error"
        try:
            WMS = driver.find_element_by_link_text("WMS").get_attribute('href')
            res[shortname]['WMS_Link'] = WMS
        except NoSuchElementException:
            res[shortname]['WMS_Link'] = "Error"
        # Get iframe details
        # Find esri map iframe, have to grab it separately from google iframe on the page. This can be done by getting a
        # div that contains the desired iframe, then selected from that element based on the iframe tag
        try:
            iframeElement = driver.find_element_by_class_name("field-name-field-map-iframe").find_element_by_tag_name(
                'iframe')
            # Pull the web map link the iframe is pointing to, split it at "&extent" to just get the link
            # without URL parameters
            webmaplink = iframeElement.get_attribute('src').split("&extent")[0]
            res[shortname]['Iframe_Webmap_Link'] = webmaplink
            # Pull web map ID
            res[shortname]['Iframe_Webmap_ID'] = webmaplink.split("webmap=")[1]
        except NoSuchElementException:
            res[shortname]['Iframe_Webmap_Link'] = "Error"
            res[shortname]['Iframe_Webmap_ID'] = "Error"
        # Get PDF details
        try:
            PDFDiv = driver.find_element_by_class_name("pane-node-field-map-pdf")
            res[shortname]['PDF_Link_Text'] = PDFDiv.find_element_by_tag_name("a").text
            res[shortname]['PDF_Download_Link'] = PDFDiv.find_element_by_tag_name("a").get_attribute('href')
            res[shortname]['PDF_File_Size'] = PDFDiv.find_element_by_class_name("file-size").text
        except NoSuchElementException:
            res[shortname]['PDF_Link_Text'] = "Error"
            res[shortname]['PDF_Download_Link'] = "Error"
            res[shortname]['PDF_File_Size'] = "Error"

        # This code lets you enter a iframe and grab its details then return to the normal page, don't need this for now
        # Enter iframe to scrape details of iframe DOM
        # driver.switch_to.frame(iframeElement)
        # Leave iframe
        # driver.switch_to.default_content()
    return res


def checklinks(gallerylinks):
    """

    :param gallerylinks: Existing dictionary populated with GIS relevant details, will be mutated
    :return: Nothing, mutates existing galleryLink dictionary with new second level keys and values
    """
    # Loop over all map keys, maps on the gallery
    for map_key in gallerylinks.keys():
        print(f"Checking links for {map_key}")
        # loop over all map gallery values in nested dictionary
        # for id_key in gallerylinks[map_key].keys():
        for id_key in link_values:
            # Check to see if id key value should contain a link to check
            # If previous attempt to find link returned an error, mark the status as the same
            if gallerylinks[map_key][id_key] == "Error":
                gallerylinks[map_key][id_key + "_Status"] = "Error"
            else:
                # Get URL to check from dictionary value
                URL = gallerylinks[map_key][id_key]
                # get web page
                driver.get(URL)
                # Get web page source text
                page_text = driver.page_source
                # Check to see if page source text contains any common error messages
                # Selenium can't directly test HTTP error messages(401,404,etc)
                valid_link = any(i in page_text for i in error_msg)
                if valid_link:
                    gallerylinks[map_key][id_key + "_Status"] = "Error"
                else:
                    gallerylinks[map_key][id_key + "_Status"] = "Active"
            # Check if any entries with WFS errors are Raster layers as they should only have WMS services
            # Only checks the first layer, at "/0" in the service, we don't currently have any raster services
            # with multiple layers
        if gallerylinks[map_key]['WFS_Link'] == "Error":
            try:
                url = str(gallerylinks[map_key]['REST_Link']) + "/0"
                driver.get(url)
                if "Raster Layer" in driver.page_source:
                    gallerylinks[map_key]['WFS_Link'] = "NA-Raster"
                    gallerylinks[map_key]['WFS_Link_Status'] = "NA-Raster"
            except InvalidArgumentException:
                print(f"Error checking if the following is a raster layer: {gallerylinks[map_key]}")
                gallerylinks[map_key]['WFS_Link_Status'] = "Error"
    return gallerylinks

def dictsumvalue(gallerylinks):
    """
    Checks all nested second level entries for error values and populates a new second level key with the results.
    This allows for a single column to be checked for an error statement in the output CSV.

    :param gallerylinks:
    :return: Nothing, mutates galleryLinks dictionary
    """
    for map_keys in gallerylinks.keys():
        if "Error" in gallerylinks[map_keys].values():
            gallerylinks[map_keys]["Summary Status"] = "Error"
        else:
            gallerylinks[map_keys]["Summary Status"] = "No problem"


# Kick off script:
# Starting URL, gallery page 1
URL = "https://www.cityofsalinas.org/our-government/information-center/map-gallery"
# Total map gallery pages
pages = int(totalpages(URL))
# Empty list of web gallery web pages that need to be visited
links_to_visit = []
# Visit page 1 and extend list with results
links_to_visit.extend(gallery_links_visit(URL))
# Loop through remaining map gallery pages extending the list of links of map gallery entries
# First page of gallery doesn't contain "page=", this starts on the second page with "page=1", loop accounts for this
for page in range(1, (pages + 1)):
    URL = (f"https://www.cityofsalinas.org/our-government/information-center/map-gallery?page={page}")
    print(f"visting URL {URL}")
    links_to_visit.extend(gallery_links_visit(URL))

# Build out the galleryLinks dictionary
gallerylinks = galleryentries(links_to_visit)
gallerylinks = checklinks(gallerylinks)
print(gallerylinks)
dictsumvalue(gallerylinks)

# Write dictionary to CSV
# This solution used as reference to write the dict to csv:
# https://stackoverflow.com/a/29400823
print("Writing csv")
with open(output_csv, "w", newline='') as csvfile:
    w = csv.DictWriter(csvfile, csv_fields)
    w.writeheader()
    for k in gallerylinks:
        w.writerow({field: gallerylinks[k].get(field) or k for field in csv_fields})
print(f"CSV written to: {output_csv}")
print(f"All done! This script took {round(time.time() - start_time, 2)} seconds to run!")
