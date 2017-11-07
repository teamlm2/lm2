class UserRight:

    def __init__(self):
        pass

    role_management = "role_management"
    land_office_admin = "land_office_administration"
    cadastre_view = "cadastre_view"
    cadastre_update = "cadastre_update"
    contracting_view = "contracting_view"
    contracting_update = "contracting_update"
    reporting = "reporting"
    application_update = "application_update"
    application_view = "application_view"


class ApplicationType:

    def __init__(self):
        pass

    pasture_use = 26  # r
    legitimate_rights = 27  # r

class PersonType:

    def __init__(self):
        pass

    legally_capable_mongolian = 10
    legally_uncapable_mongolian = 20
    mongolian_buisness = 30
    mongolian_state_org = 40
    foreign_citizen = 50
    legal_entity_foreign = 60

