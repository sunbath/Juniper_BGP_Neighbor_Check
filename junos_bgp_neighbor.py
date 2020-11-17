import ipaddress
import re
import pyperclip

def command_prompt_read_multilines(prompt_text, stopword):
    text = ""
    print(prompt_text)
    while True:
        line = input()
        if line.strip() == stopword:
            break
        text += "%s\n" % line
    return text


def ip_address_extractor(text):
    ipPattern = re.compile(
        r'(?:25[0-4]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[1-9])\.(?:25[0-4]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(?:25[0-4]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(?:25[0-4]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\/(?:3[0-2]|2[0-9]|1[0-9]|[1-9])$')
    ip_address_with_netmask = re.findall(ipPattern, text)
    if re.search(ipPattern, text) == None:
        return "Invalid IP Address"
    else:
        return ipaddress.ip_interface(ip_address_with_netmask[0])


def vendor_detect(text):
    junos_commandPattern = re.compile('sh[a-z]* int[a-z]* terse \| match')
    cisco_commandPattern = re.compile('sh[a-z]* ip int[a-z]* bri[a-z]* \| in ')

    if re.findall(cisco_commandPattern, text):
        return 'cisco'
    elif re.findall(junos_commandPattern, text):
        return 'juniper'
    else:
        return 'unknown'


def get_show_interface_output():
    stopword = "END"
    prompt_text = "Please paste your interface command output below (e.g. show interfaces terse | match ge-1/3/1) \nStop Word: \"END\""
    interface_input = command_prompt_read_multilines(prompt_text, stopword)
    vendor = vendor_detect(interface_input.splitlines()[0])
    interface_input_list = [y for y in (x.strip() for x in interface_input.splitlines()) if "inet" in y]
    ip_address_list = [ip_address_extractor(x) for x in interface_input_list if
                       ip_address_extractor(x) != "Invalid IP Address"]
    return ip_address_list, vendor


def get_neigbor_ip(interface_ip_with_mask):
    network_address = ipaddress.ip_network(interface_ip_with_mask, strict=False)
    host_ip_list = list(network_address.hosts())
    neighbor_ip_list = [x for x in host_ip_list if x != interface_ip_with_mask.ip]
    return neighbor_ip_list


def show_bgp_neighbor_command_generator(vendor, neighbor_ip_list):
    junos_command = "show bgp summary | match "
    cisco_command = "show ip bgp summary | in "
    arista_command = "show ip bgp summary | in "

    if vendor == 'juniper':
        neighbor_list = "|".join(str(x) for x in neighbor_ip_list)
        command = junos_command + "\"" + neighbor_list + "\""
    elif vendor == "cisco":
        neighbor_list = "|".join(str(x) for x in neighbor_ip_list)
        command = cisco_command + neighbor_list
    elif vendor == "arista:":
        neighbor_list = "|".join(str(x) for x in neighbor_ip_list)
        command = arista_command + neighbor_list

    return command


def main():
    interface_ip_list, vendor = get_show_interface_output();

    if vendor == 'unknown':
        print("\n")
        print("Sorry, this script only supports Cisco IOS, Juniper and Arista.\nPlease try again!")
    else:
        print("\n")
        print("This is the {} command: \n".format(vendor.capitalize()))
        neighbor_ip_list = [y for x in interface_ip_list for y in get_neigbor_ip(x)]
        print(show_bgp_neighbor_command_generator(vendor, neighbor_ip_list))
        #pyperclip.copy(show_bgp_neighbor_command_generator(vendor, neighbor_ip_list))
        #pyperclip.paste()


if __name__ == "__main__":
    main()