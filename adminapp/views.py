from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.db.models import Max

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from .models import Student, StudentInfo
from django.http import Http404

from django.contrib import messages

from adminapp.serializers import StudentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)

def user_login(request):
    context = RequestContext(request)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                if user.is_superuser:
                    login(request, user)
                    messages.add_message(request, messages.SUCCESS, "You are now logged in.")
                    return redirect('/menu/')
                else:
                    return HttpResponse("Your account doesn't have access to this page. To proceed, please login with an account that has access.")  
            else:
            	messages.add_message(request, messages.ERROR, "Your account is disabled. To proceed, please login with an account that is active.")
            	return redirect('/')
        else:
            messages.add_message(request, messages.ERROR, "Your username and password didn't match. Please try again.")
            return redirect('/')

    # The request is not a HTTP POST, so display the login form.
    else:
        return render(request, 'index.html', context)

# login_required() decorator to ensure only those logged in can access the view.
@login_required(login_url='/login/')
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    messages.add_message(request, messages.INFO, "You have been logged out.")
    # Take the user back to the homepage.
    return redirect('/')

        
class MenuPageView(TemplateView):
    template_name = "menu.html"

class AddPageView(TemplateView):
    template_name = "addStudents.html"
    
    def get(self, request, **kwargs):
        try:	
            classes = StudentInfo.objects.all().aggregate(Max('class_no'))
        except (Student.DoesNotExist) as e:
            raise Http404('StudentInfo does not exist')
        return render(request, self.template_name,
                      {'classes': classes})
                      

class StatisticsPageView(TemplateView):

    template_name = 'statistics.html'
	
    def get(self, request, **kwargs):
        try:	
            students = Student.objects.all()
            all_students = students.count()
            deceased = students.filter(deceased=1).count()
            graduates = students.filter(student_info__grad_or_student='grad').count()
            dropouts = students.filter(student_info__dropout=1).count()
            employed = students.filter(employment_info__current_employment__isnull=False).count()
            unemployed = students.filter(employment_info__current_employment__isnull=True).count()
            classes = StudentInfo.objects.all().aggregate(Max('class_no'))
            years = StudentInfo.objects.all().aggregate(Max('year'))
        except (Student.DoesNotExist) as e:
            raise Http404('Student does not exist')
        return render(request, self.template_name,
                      {'all_students': all_students, 'deceased': deceased, 'graduates': graduates, 'dropouts': dropouts, 'employed': employed, 'unemployed': unemployed, 'classes': classes, 'years': years})

@login_required(login_url='/login/')			
def filter(request):
    yearstart = request.POST.get('yearstart') 
    yearend = request.POST.get('yearend')
    classstart = request.POST.get('classstart')
    classend = request.POST.get('classend')
    if (yearstart and yearend) is not None:
        students = Student.objects.filter(student_info__year__range=(yearstart, yearend))
    elif (classstart and classend) is not None:
    	students = Student.objects.filter(student_info__class_no__range=(classstart, classend))
    data = {'all_students': students.count(), 'deceased': students.filter(deceased=1).count(), 'graduates': students.filter(student_info__grad_or_student='grad').count(), 'dropouts': students.filter(student_info__dropout=1).count(), 'employed': students.filter(employment_info__current_employment__isnull=False).count(), 'unemployed': students.filter(employment_info__current_employment__isnull=True).count()}
    return render(request, 'table.html', data)
 
def handle_uploaded_file(file, filename):
	with open('static/' + filename, 'wb+') as destination:
		for chunk in file.chunks():
			destination.write(chunk)   



class StudentList(APIView):
    def get(self, request, format=None):
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        sname = request.data['name']
        sid_no = request.data['id_no']
        try:
            obj = Student.objects.get(name=sname, id_no=sid_no)
            messages.add_message(request._request, messages.INFO, "Student is already in database")
        except Student.DoesNotExist:
            try:
            	handle_uploaded_file(request.FILES['image'], str(request.FILES['image']))
            except:
            	serializer = StudentSerializer(data=request.data)
            	if serializer.is_valid():
                	serializer.save()
                	return Response(serializer.data, status=status.HTTP_201_CREATED)
            	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponse('An error occured')

        

