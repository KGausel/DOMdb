"""
MIT License

Copyright (c) 2019 KGausel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Authors: Kristian Gausel and Søren Qvist Jensen
WARNING: THIS IS NOT A SERIOUS PRODUCT
"""
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import uuid
import time
import os

browser = None

def query(qs):
    elements = browser.find_element_by_css_selector("body").find_elements_by_css_selector(qs)
    return [serialize(element) for element in elements]

def find_row_id(element):
    r_id = element.get_attribute("id")
    while not r_id:
        element = element.find_element_by_xpath('..')
        r_id = element.get_attribute("id")
    return r_id

def serialize_element_to_object(element):
    if element.tag_name == "p":
        if element.get_attribute("type") == "bool":
            return not element.text == "false"
        elif element.get_attribute("type") == "int":
            return int(element.text)
        elif element.get_attribute("type") == "number":
            return float(element.text)
        elif element.get_attribute("type") == "string":
            return str(element.text)
    elif element.tag_name == "li":
        return serialize_element_to_object(element.find_element_by_xpath("*"))
    elif element.tag_name == "ol":
        return [serialize_element_to_object(child) for child in element.find_elements_by_xpath("li")]
    elif element.tag_name == "div":
        if element.get_attribute("id"):
            # "document"
            return serialize_element_to_object(element.find_element_by_xpath("*"))
        elif element.get_attribute("type") == "object":
            return_dict = {}
            for child in element.find_elements_by_xpath("*"):
                key = child.get_attribute("key")
                value = serialize_element_to_object(child.find_element_by_xpath("*"))
                return_dict[key] = value
            return return_dict
        else:
            key = element.get_attribute("key")
            value = serialize_element_to_object(element.find_element_by_xpath("*"))
            return {key: value}


def serialize(element):
    row_id = find_row_id(element)
    return {"id": row_id, "doc": serialize_element_to_object(element)}

def _insert_object(obj):
    browser.execute_script("""
        const obj = arguments[0];
        const obj_id = obj["id"];
        const obj_doc = obj["doc"];
        const obj_classified = obj["classified"]
        
        function createPrimitive(typ, data){
                const n = document.createElement("p");
                n.setAttribute("type", typ);
                n.appendChild(document.createTextNode(data));
                return n
        }

        function buildObject(data) {
            if(typeof data === 'string'){
                return createPrimitive("string", data);
            } else if(typeof data === 'number'){
                if(Number.isInteger(data)){
                   return createPrimitive("int", data);
                } else {
                   return createPrimitive("number", data);
                }
            } else if(typeof data === 'boolean') {
                return createPrimitive("bool", data);
            }

            else if(Array.isArray(data)) {
                const n = document.createElement("ol");
                 for (var elem in data) {
                        let d = document.createElement("li");
                        d.appendChild(buildObject(data[elem]))
                        n.appendChild(d)
                }
                return n
            }

            else if(typeof data === 'object'){
                const n = document.createElement("div");
                n.setAttribute("type", "object");
                for (var key in data) {
                    if (data.hasOwnProperty(key)) {
                        let d = document.createElement("div");
                        d.setAttribute("key", key)
                        d.appendChild(buildObject(data[key]))
                        n.appendChild(d)
                    }
                }
                return n
            }


        }
        const newObject = buildObject(obj_doc);

        const wrapper = document.createElement("div");
        wrapper.setAttribute("id", obj_id)
        if(obj_classified){
            wrapper.setAttribute("class", obj_classified)
        }
        wrapper.appendChild(newObject);
        document.getElementsByTagName("body")[0].appendChild(wrapper);
        """, obj)

def insert_object(doc, classified = False):
    uid = "dom" + uuid.uuid4().hex[:7]

    obj_to_insert = {"id": uid, "doc": doc}
    if classified:
        obj_to_insert["classified"] = classified
    _insert_object(obj_to_insert)
    return uid

def delete_object(oid):
    browser.execute_script("""
        function removeElement(elementId) {
            // Removes an element from the document
            var element = document.getElementById(elementId);
            element.parentNode.removeChild(element);
        }
        removeElement(arguments[0]);
    
    """, oid)

def snapshot(saveto, pixelbytes=None):
    if pixelbytes:
        old_window = browser.get_window_rect()
        browser.set_window_size(1920, pixelbytes)
    result = browser.get_screenshot_as_file(saveto)
    if pixelbytes:
        browser.set_window_rect(**old_window)
    return result

tables = {"default": None}

with open(os.path.join(os.path.dirname(__file__), "table_template.temp"), "r") as tf:
    _init_template = tf.read()

def new_TABle(name, seedpath=None):
    if name in tables: return
    browser.execute_script("window.parent = window.open('parent');")

    for handle in browser.window_handles:
        if handle not in tables.values():
            break

    tables[name] = handle
    browser.switch_to.window(handle)
    _set_database(_init_template.replace("<title>default | DOMdb</title>", "<title>" + name + " | DOMdb</title>"))

def select_table(name, seedpath=None):
    if name not in tables:
        new_TABle(name)
    browser.switch_to.window(tables[name])
    if seedpath is not None:
        _set_database(_import_database(seedpath))

def _set_database(data):
    browser.execute_script("""
        document.write(arguments[0]);
    """, data)

def _get_database():
    return browser.page_source

def export_database(filepath):
    data = _get_database()
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data)

def _import_database(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def import_database(seedpath):
    _set_database(_import_database(seedpath))

#print(query('#testdicts'))

#insert_object([1,2213,3])

#insert_object(query('#testdicts')[0]["doc"])

#browser.switch_to.window("test")

if __name__ == "__main__":
    import argparse
    import pyfiglet
    os.environ["PYTHONINSPECT"] = "true"

    print(pyfiglet.figlet_format("DOM db", font="slant"))
    arguments = argparse.ArgumentParser(description="A modern in-memory domcument database")
    arguments.add_argument("--debug", default=False, action="store_true", help="Start DOMdb in debug / interactive mode")
    arguments.add_argument("--demo", default=False, action="store_true", help="Run a demo of how DOMdb works!")

    args, rem = arguments.parse_known_args()

    options = webdriver.ChromeOptions()
    if not args.debug:
        options.add_argument('headless')


    browser = webdriver.Chrome(options=options)

    browser.get("about:blank")
    browser.execute_script(f"""
    document.write(`
        {_init_template.replace("<title>default | DOMdb</title>", "<title>" + "default" + " | DOMdb</title>")}
    `);
    """)
    tables["default"] = browser.current_window_handle

    insert = insert_object
    TABle = select_table
    DOMp = export_database

    def pquery(*args, **kwargs):
        result = query(*args, **kwargs)
        print()
        print(json.dumps(result, indent=4))
        print()

    queries = [
        "div ol :nth-child(2)",
    ]

    def _atexit():
        browser.quit()
    import atexit
    atexit.register(_atexit)

    def clear_repl(title=None):
        #print("\n" * 100)
        #print("\033[2J")

        input("... ")
        os.system("cls")
        if title:
            print(pyfiglet.figlet_format(title))

    def demo():
        os.system("cls")
        print(pyfiglet.figlet_format("Introducing DOMdb"))
        print()
        print("[*] A new in-memory, ephemeral, GDPR-compliant domcument database")
        print("[-] Finally, a frontend-friendly database")

        clear_repl("Core features")
        print("[*] Built on top of the powerful V8 Engine")
        print("[*] Familiar query language that is fully CSS compliant")
        print("[*] Data presentation layer is fully customizable")
        print("[*] Deep data insight using the built-in debug mode")
        print("[*] Includes developer tools and advanced data inspection capabilities")
        print("[*] Support for advanced delta-updates through familiar UI")
        print("[*] Multi-TABle support")
        print("[*] Supreme backup- and snapshot capabilities")

        clear_repl("Insert document")
        obj1 = {"We have lists": [1, "hello", True], "And primitives": "a string", "and objects": {"that": "can nest", "ofcourse": [1]}}
        print("Let us insert an object: ")
        print(f">>> insert({json.dumps(obj1, indent=4)})")
        key1 = insert(obj1)
        input("... ")
        print("This gets assigned a unique key:")
        print(key1)

        clear_repl("Query")
        print("\nWhich of course can be queried")
        print(f">>> query(\"#{key1}\")")
        print(">>>")
        result = query(f"#{key1}")
        print(f"{json.dumps(result,indent=4)}")
        input("... ")
        print("\nThe query language has full CSS selector support")
        input("... ")
        print("\nFor example: we can query all the strings in our inserted data")
        print(f">>> query('p[type=\"string\"]')")
        result = query("p[type=\"string\"]")
        print(">>>")
        print(json.dumps(result, indent=4))

        clear_repl("Snapshot")
        print("\nThere is also a powerful snapshot feature")
        print(">>> snapshot(\"snapshot.png\", pixelbytes=250)")
        snapshot("snapshot.png", pixelbytes=250)
        TABle("temp")
        browser.get("file://" + os.path.abspath("snapshot.png"))
        input("... ")
        browser.close()
        TABle("default")
        del tables["temp"]
        time.sleep(2)
        clear_repl("TABles")
        print("\nThere is of course support for multiple TABles")
        TABle("new")
        print("Which are independent from other TABles")
        print(">>> insert(...)")
        insert({"row1": "row1", "elem1": ["item 1", "item 2", "item 3", "item 4", "item 5"]})
        insert({"row2": "row2", "elem2": ["item 1", "item 2", "item 3", "item 4", "item 5"]})
        insert({"row3": "row3", "elem3": ["item 1", "item 2", "item 3", "item 4", "item 5"]})


        clear_repl("GDPR")
        TABle("default")
        print("\nWe are also using advanced auto-masking technology to hide sensitive information")
        insert({"username": "username", "password": "secret stuff"})
        input("... ")
        print("\nOr we can insert items as classified")
        obj2 = {"We have lists": [1, "hello", True], "And primitives": "a string",
                "and objects": {"that": "can nest", "ofcourse": [1]}}
        print(f">>> insert({json.dumps(obj2, indent=4)}, classified=True)")
        key2 = insert(obj2, classified=True)
        input("... ")
        print("\nThe data can still be queried:")
        print(f">>> query('#{key2}')")
        result = query(f"#{key2}")
        print(">>>")
        print(json.dumps(result, indent=4))

        clear_repl("DOMping")
        print("\nYou can of course also DOMp your database")
        print(">>> DOMp(\"DB_DOMp.dom\")")
        DOMp("DB_DOMp.dom")

        input("... ")
        print("\nAnd grow a TABle using the DOMp as a seed")
        print(">>> TABle(\"imported\", \"DB_DOMp.dom\")")
        TABle("imported", "DB_DOMp.dom")

        clear_repl("Questions?")


    if args.demo:
        demo()
