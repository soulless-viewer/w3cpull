from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException,
    NoSuchElementException,
)
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
from datetime import (
    datetime,
    timezone
)
from selenium import webdriver
import logging as log
import urllib.parse
import threading
import requests
import hashlib
import shutil
import glob
import time
import sys
import os

DOWNLOAD_THREADS = []

def init(module_dir, selenium_target_dir, selenium_temp_download_dir, visual, browser):
    if not os.path.exists(selenium_target_dir):
        os.mkdir(selenium_target_dir)
    if not os.path.exists(selenium_temp_download_dir):
        os.mkdir(selenium_temp_download_dir)

    log.basicConfig(
        stream=sys.stdout,
        level=log.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    browser_case = {
        "chrome": chrome_init,
        "firefox": firefox_init,
        None: firefox_init
    }
    browser_init = browser_case[browser]
    return browser_init(module_dir, selenium_temp_download_dir, visual)

def chrome_init(module_dir, selenium_temp_download_dir, visual):
    profile = webdriver.ChromeOptions()
    profile.add_experimental_option("prefs",{
        "download.default_directory": selenium_temp_download_dir,
        "download.prompt_for_download": False,
        "profile.password_manager_enabled": True
    })
    if not visual:
        profile.add_argument("--headless")

    return webdriver.Chrome(executable_path = os.path.join(module_dir, 'chromedriver'), chrome_options=profile)


def firefox_init(module_dir, selenium_temp_download_dir, visual):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.cache.disk.enable", False)
    profile.set_preference("browser.cache.memory.enable", False)
    profile.set_preference("browser.cache.offline.enable", False)
    profile.set_preference("network.http.use-cache", False)
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", selenium_temp_download_dir)
    with open(os.path.join(module_dir, "mime-types.txt"), "r") as mime:
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", mime.read())
        mime.close()

    if not visual:
        options = Options()
        options.headless = True
        return webdriver.Firefox(profile, executable_path = os.path.join(module_dir, "geckodriver"), options=options)
    else:
        return webdriver.Firefox(profile, executable_path = os.path.join(module_dir, "geckodriver"))

def check_if_url_accessible(url):
    try:
        response = requests.get(url)
        return True
    except requests.ConnectionError as exception:
        return False

def w3id_auth(driver, w3id_login = None, w3id_password = None):
    if (w3id_login == None or w3id_password == None):
        log.info("Authentication data is expected to be entered in the browser...")
        def auth_waiting():
            try:
                ui.WebDriverWait(driver, 60).until(EC.title_contains("Overview"))
            except TimeoutException:
                auth_waiting()
        auth_waiting()

    else:
        username = driver.find_element_by_id("desktop")
        username.clear()
        username.send_keys(w3id_login)

        password = driver.find_element_by_name("password")
        password.clear()
        password.send_keys(w3id_password)
        clickw(driver, driver.find_element_by_id("btn_signin"))

def create_download_thread(url, path):
    r = requests.get(url, stream=True, allow_redirects=True)
    with open(
        os.path.join(
            path, urllib.parse.unquote(url.rsplit("/", 1)[1].rsplit("?", 1)[0])
        ), 'wb') as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)

def download_file(url, path):
    global DOWNLOAD_THREADS

    download_thread = threading.Thread(target=create_download_thread, args=(url, path))
    DOWNLOAD_THREADS.append(download_thread)
    download_thread.start()


def wait_community_page_load(driver):
    ui.WebDriverWait(driver, 30).until(EC.title_contains("Overview"))

def wait_wiki_page_load(driver):
    ui.WebDriverWait(driver, 30).until(EC.title_contains("Wiki"))


def clickw(driver, el):
    try:
        el.click()
    except ElementNotInteractableException:
        driver.execute_script("arguments[0].click();", el)


def get_wiki_tree(driver, wikis_menu_html):
    full_tree = []
    for child in wikis_menu_html.find_elements_by_xpath("./div"):
        wiki_tree = {}
        el = child.find_element_by_xpath("./div[1]/span[2]/a")
        wiki_tree["url"] = el.get_attribute("href")
        wiki_tree["name"] = el.get_attribute("title")
        wiki_tree["subwiki"] = []
        el = child.find_element_by_xpath("./div[1]/img[2]")
        driver.execute_script("arguments[0].click();", el)
        el = child.find_element_by_xpath("./div[2]")
        if not str(el.get_attribute("childElementCount")) == "0":
            for item in get_wiki_tree(driver, el):
                wiki_tree["subwiki"].append(item)
        full_tree.append(wiki_tree)

    return full_tree


def create_fs_tree(root_path, communities_tree):
    root_path = os.path.join(root_path, communities_tree["name"])
    try:
        os.mkdir(root_path)
    except FileNotFoundError:
        os.mkdir(root_path)

    communities_tree["comm_path"] = root_path

    def deep_dive(root, tree):
        for item in tree:
            wiki_path = os.path.join(
                root,
                urllib.parse.unquote(item["url"].rsplit("?", 1)[0].rsplit("/", 1)[1]),
            )
            os.mkdir(wiki_path)
            item["wiki_path"] = wiki_path

            links_path = os.path.join(wiki_path, "links")
            os.mkdir(links_path)
            item["links_path"] = links_path

            attachments_path = os.path.join(wiki_path, "attachments")
            os.mkdir(attachments_path)
            item["attachments_path"] = attachments_path

            if len(item["subwiki"]) > 0:
                deep_dive(wiki_path, item["subwiki"])

    deep_dive(root_path, communities_tree["wikis"])
    if len(communities_tree["subcomm"]) > 0:
        for item in communities_tree["subcomm"]:
            item = create_fs_tree(communities_tree["comm_path"], item)

    return communities_tree


def move_content(src, dst):
    moved = []
    for item in glob.glob('{}/*'.format(os.path.abspath(src))):
        moved.append(shutil.move(item, os.path.abspath(dst)))

    return moved


def download_to_dir(url, path):
    r = requests.get(url, allow_redirects=True)
    open(
        os.path.join(
            path, urllib.parse.unquote(url.rsplit("/", 1)[1].rsplit("?", 1)[0])
        ),
        "wb",
    ).write(r.content)


def download_wiki(driver, wiki_name, wiki_path, wiki_links_path, wiki_attachments_path, selenium_temp_download_dir):
    # Download Wiki
    el = driver.find_element_by_xpath('//a[contains(text(), "Page Actions")]')
    driver.execute_script("arguments[0].click();", el)
    clickw(
        driver, driver.find_element_by_xpath('//td[contains(text(), "Download Page")]')
    )
    move_content(selenium_temp_download_dir, wiki_path)
    log.info('--- {} done'.format(wiki_name))
    # Download Wiki links
    el = driver.find_element_by_xpath('//div[@id="wikiContentDiv"]')
    download_wiki_links(el, wiki_links_path)
    log.info('------ {} (links) done'.format(wiki_name))
    # Download Wiki Attachments
    clickw(driver, driver.find_element_by_xpath('//*[@id="attachments_link"]'))
    el = driver.find_element_by_xpath('//div[@id="attachments"]')
    download_wiki_attachments(el, wiki_attachments_path)
    log.info('------ {} (attachments) done'.format(wiki_name))


def download_wiki_links(el, path):
    try:
        for child in el.find_elements_by_xpath('.//a[contains(@href, "/api/")]'):
            download_file(child.get_attribute("href"), path)
    except NoSuchElementException:
        return None


def download_wiki_attachments(el, path):
    try:
        for child in el.find_elements_by_xpath(".//tbody/tr"):
            download_file(
                child.find_element_by_xpath(".//a").get_attribute("href"), path
            )
        next = el.find_element_by_xpath(
            '//*[@id="wikiPageAttachments"]/div[1]/ul[1]/li[4]'
        )
        if not str(next.get_attribute("childElementCount")) == "0":
            next.find_element_by_xpath("./a").click()
            download_wiki_attachments(el, path)
    except NoSuchElementException:
        return None


def open_wiki_section(driver):
    el = ui.WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "dropdownNavMenuTitleLink"))
    )
    clickw(driver, el)
    el = driver.find_element_by_id("lotusNavBar")
    for child in el.find_elements_by_xpath(".//*"):
        if child.get_attribute("widgetdefid") == "Wiki":
            driver.get(child.find_element_by_xpath("./a").get_attribute("href"))
            wait_wiki_page_load(driver)
            break


def download_community(driver, tree, selenium_temp_download_dir):
    global DOWNLOAD_THREADS

    def deep_dive(wikis):
        for wiki in wikis:
            driver.get(wiki["url"])
            wait_wiki_page_load(driver)
            download_wiki(
                driver,
                wiki["name"],
                wiki["wiki_path"],
                wiki["links_path"],
                wiki["attachments_path"],
                selenium_temp_download_dir
            )
            if len(wiki["subwiki"]) > 0:
                deep_dive(wiki["subwiki"])
    deep_dive(tree["wikis"])
    if len(tree["subcomm"]) > 0:
        for subcomm in tree["subcomm"]:
            download_community(driver, subcomm, selenium_temp_download_dir)

    for t in DOWNLOAD_THREADS:
        t.join()



def create_communities_tree(driver, community_url, recursive, w3id_login = None, w3id_password = None):
    communities_tree = {}
    driver.get(community_url)

    if driver.title == "IBM w3id":
        w3id_auth(driver, w3id_login, w3id_password)
    wait_community_page_load(driver)

    communities_tree["name"] = driver.title[11:]
    communities_tree["url"] = community_url

    communities_tree["wikis"] = []
    open_wiki_section(driver)
    wikis_menu_html = driver.find_element_by_xpath(
        '//div[@id="lconnWikisNavTree"]/div[2]/div[2]'
    )
    wikis_tree = get_wiki_tree(driver, wikis_menu_html)
    communities_tree["wikis"] = wikis_tree
    log.info("--- {} (wiki) done".format(communities_tree["name"]))

    communities_tree["subcomm"] = []

    if recursive:
        driver.get(community_url)
        wait_community_page_load(driver)
        el = driver.find_element_by_xpath('//*[@id="dropdownSubMenuContainer"]')
        if not "lotusHidden" in el.get_attribute("class"):
            sub_links = []
            for child in el.find_elements_by_xpath(
                './div[@id="dropdownSubMenu"]//div/div/div/ul/li'
            ):
                sub_links.append(child.find_element_by_xpath("./a").get_attribute("href"))
            for sub_link in sub_links:
                communities_tree["subcomm"].append(
                    create_communities_tree(driver, sub_link, w3id_login, w3id_password)
                )
            log.info("--- {} (subcommunities)  done".format(communities_tree["name"]))
        log.info("--- {}  done".format(communities_tree["name"]))

    return communities_tree


def finish(driver):
    driver.close()
