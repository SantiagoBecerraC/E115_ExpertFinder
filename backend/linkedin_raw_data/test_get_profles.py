from linkedin_api import Linkedin

api = Linkedin("hjy.alder@outlook.com", "Abced12sg!", refresh_cookies=True)
urn = "ACoAAD2zAhsB9-kge1ICtZ8u84N4wtVsxY7PD1o"
profile = api.get_profile(urn_id=urn)
print(profile)
