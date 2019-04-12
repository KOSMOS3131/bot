import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.append("/root/bot")

# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from data.models import Statistic

def print_table(table):
    col_width = [max(len(x) for x in col) for col in zip(*table)]
    for line in table:
        print ("| " + " | ".join("{:{}}".format(x, col_width[i])
                                for i, x in enumerate(line)) + "  |")

if __name__ == '__main__':
    stats = Statistic.objects.all().order_by("name")
    for stat in stats:
        stat.count = 0
        stat.save()
    print("Statistic resets!")
