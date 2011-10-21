from lizard_map.models import ExtentMixin
from lizard_map.models import PeriodMixin
from lizard_map.models import UserSessionMixin


class Period(PeriodMixin):
    """Test class to instantiate PeriodMixin"""
    pass


class Extent(ExtentMixin):
    pass


class UserSession(UserSessionMixin):
    """Test class to instantiate UserSessionMixin"""
    pass
