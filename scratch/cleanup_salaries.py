import os
import django
import sys

# Setup Django
sys.path.append('/Users/user/Kamanda-bilan-ERP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.salary.models import Salary
from apps.attendance.models import Attendance

def cleanup():
    salaries = Salary.objects.filter(is_paid=False)
    print(f"Checking {salaries.count()} unpaid salary records...")
    deleted = 0
    for s in salaries:
        has_attendance = Attendance.objects.filter(
            group__teacher=s.user, 
            date__year=s.month.year, 
            date__month=s.month.month
        ).exists() or Attendance.objects.filter(
            group__assistant=s.user, 
            date__year=s.month.year, 
            date__month=s.month.month
        ).exists()
        
        if not has_attendance:
            print(f"Deleting ghost record: {s.user.username} for {s.month}")
            s.delete()
            deleted += 1
            
    print(f"Successfully deleted {deleted} ghost records.")

if __name__ == "__main__":
    cleanup()
