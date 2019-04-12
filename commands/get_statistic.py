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
    table =[]
    for stat in stats:
        table.append([stat.name, str(stat.count)])
    print("| Task statistic |")
    print("|----------------|")
    print_table(table)
