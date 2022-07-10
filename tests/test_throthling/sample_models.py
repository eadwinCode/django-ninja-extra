from ninja_extra.throttling import UserRateThrottle


class User3SecRateThrottle(UserRateThrottle):
    rate = "3/sec"
    scope = "seconds"


class User3MinRateThrottle(UserRateThrottle):
    rate = "3/min"
    scope = "minutes"


class User6MinRateThrottle(UserRateThrottle):
    rate = "6/min"
    scope = "minutes"


class ThrottlingMockUser(str):
    is_authenticated = True
    pk = id = 23

    def set_id(self, value):
        self.pk = self.id = value
