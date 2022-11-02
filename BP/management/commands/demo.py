from django.core.management.base import BaseCommand
from BP.models import Firm, Attorney, AttorneyStaff, Client, Case, ToDo
from django.contrib.auth.decorators import login_required
import datetime


class Command(BaseCommand):
    help = "This is a demo handler"
    def handle(self, *args, **options):
        firms = Firm.objects.all()
        current_date = datetime.date.today()
        for firm in firms:
            attorney = Attorney.objects.get(attorneyprofile=firm)
            clients = Client.objects.filter(created_by=attorney)
            for client in clients:
                todos = ToDo.objects.filter(for_client=client)
                for todo in todos:
                    last_updated = todo.last_updated.date()
                    print('last_updated_date:', last_updated)
                    days = current_date - last_updated
                    days = days.days
                    if int(days) == int(todo.days_to_repeat):
                        case = todo.for_case
                        case_statuses = [x.id for x in case.auto_case_status.all()]
                        todo_statuses = [x.id for x in todo.case_status.all()]
                        print(case_statuses)
                        print(todo_statuses)
                        check = False
                        if(set(todo_statuses).issubset(set(case_statuses))):
                            check = True
                        if check:
                            print('Hello we are in')
                            new_todo = ToDo.objects.create(created_by=todo.created_by, for_client=todo.for_client, for_case=todo.for_case, due_date=todo.due_date, todo_for=todo.todo_for, notes=todo.notes, time=todo.time, days_to_repeat=todo.days_to_repeat)
                            new_todo.last_updated = datetime.datetime.now()
                            new_todo.save()
                            for x in todo.case_status.all():
                                new_todo.case_status.add(x)
                                new_todo.save()
                            todo.delete()
                            

    

        self.stdout.write("Hello, World!")