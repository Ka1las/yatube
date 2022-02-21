import datetime


def year(request):
    now = datetime.datetime.now().year
    return {'year': now}
