import os
import xml.etree.ElementTree as ET


def parse_xml_to_json(supplier_name):
    xml_file_path = os.path.join(os.getcwd(), 'xml', f'{supplier_name}.xml')

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        def elem_to_dict(elem):
            d = {elem.tag: {} if elem.attrib else None}
            children = list(elem)
            if children:
                dd = dict()
                for dc in map(elem_to_dict, children):
                    for k, v in dc.items():
                        if k in dd:
                            dd[k].append(v)
                        else:
                            dd[k] = [v]
                d = {elem.tag: dd}
            if elem.attrib:
                d[elem.tag].update(('@' + k, v) for k, v in elem.attrib.items())
            if elem.text:
                text = elem.text.strip()
                if children or elem.attrib:
                    if text:
                        d[elem.tag]['#text'] = text
                else:
                    d[elem.tag] = text
            return d

        json_from_xml = elem_to_dict(root)
        return json_from_xml
    except Exception as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
        return None

# Example usage:
# json_data = parse_xml_to_json('pgn')
# print(json_data)
