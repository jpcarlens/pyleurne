class User:

    def __init__(self, username, ip_adress, role):
        self.__username = username
        self.__ip_adress = ip_adress
        self.__role = role

    def get_pseudo(self):
        return self.__username

    def get_ip_address(self):
        return self.__ip_adress

    def get_role(self):
        return self.__role
