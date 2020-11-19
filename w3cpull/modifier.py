import os
import re

def replace_links(path):
    files_list = get_files_list(path)
    links_list = []
    for file in files_list:
        with open(file, 'r+') as f:
            content = f.read()
            matches = re.findall(r"<a.*>.*<\/a>", content)
            for match in matches:
                links = re.findall(r"href=\"([^\s]+)\"", match)
                for link in links:
                    if "/api/" in link:
                        content = content.replace(link, "./links/{}".format(link.rsplit("/", 1)[1]))
            f.truncate(0)
            f.write(content)
        f.close()

def get_files_list(path):
    target_dir = (os.path.abspath(path) if not path[0] == '~' else os.path.expanduser(path))
    list = []

    for path, dirs, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.html'):
                list.append(os.path.join(path, file))

    return list
