from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import SigninForm, CompanyCredentialsForm, RaiseInvoiceForm,ClientForm
from django.views.generic import View
from django.views import generic
from django.core.urlresolvers import reverse
from .models import Company_credentials, Invoice,Client
from django.core.mail import send_mail, EmailMessage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import landscape
import datetime
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.pdfgen.canvas import Canvas
from django.forms import modelformset_factory
from django.views.generic.edit import UpdateView

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'invoiceapp/index.html', {'message': 'You have successfully logged in'})
            return render(request, 'invoiceapp/index.html',
                          {'message': 'Your Account is not Active, Contact the Administrator'})
        return render(request, 'invoiceapp/login.html', {'message': 'Wrong Username or Password'})
    else:
        if request.user.is_authenticated():
            return render(request, 'invoiceapp/index.html', {'message': 'Already logged in'})
        else:
            return render(request, 'invoiceapp/login.html')


def logout_user(request):
    if request.user.is_authenticated():
        logout(request)
        return render(request, 'invoiceapp/index.html', {'message': 'You have successfully logged out',})
    return render(request, 'invoiceapp/login.html', {'message': 'log in first'})


class Account(View):
    form_class = CompanyCredentialsForm
    template_name = 'invoiceapp/account.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect(reverse('invoiceapp:index'))

        return render(request, self.template_name, {'message': 'Fill your credentials again'})


class AccountUpdate(UpdateView):
    model = Company_credentials
    fields = ['email','company_name','company_address','country','phone_number','website_url']
		
		
class Index(View):
    form_class = SigninForm
    template_name = "invoiceapp/index.html"

    def get(self, request):
        logged = False
        if request.user.is_authenticated():
            logged = True
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form,'logged':logged})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            user.set_password(password)
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                return redirect(reverse('invoiceapp:account'))

            return render(request, self.template_name, {'message': 'Sign in again ', 'form': form,})
        return render(request, self.template_name, {'message': 'Sign in again ', 'form': form,})




def generate_certificate(description_of_items,cost_of_items,amount,cost,qty,raise_for,request ):

    buffer = BytesIO()
    styleSheet = getSampleStyleSheet()
    style = styleSheet['Normal']
    canv = Canvas('my_pdf.pdf')
    canv.setFillColorRGB(0, 0, 255)
    canv.setFont('Helvetica-Bold', 44, leading=None)
    canv.drawCentredString(102, 800, "INVOICE")
    canv.setFont('Helvetica-Bold', 8, leading=None)
    #canv.drawCentredString(38, 824, "From:")
    b = Company_credentials.objects.get(user=request.user)
    canv.setFillColorRGB(0, 0, 255)
    canv.drawCentredString(480, 826, b.company_name)
    canv.drawCentredString(480, 813, b.email)
    canv.drawCentredString(480, 801, b.country + ',' + b.phone_number)
    #canv.drawCentredString(480, 790, b.email)
    canv.setFillColorRGB(0, 0, 0)

    canv.drawCentredString(480, 790, "Raised on:" + str(datetime.date.today()) )
    canv.line(0, 785, 800, 785)
    canv.setFont('Helvetica', 21, leading=None)
    canv.setFillColorRGB(0, 0, 255)
    canv.drawCentredString(68, 760, "Description:")
    canv.setFillColorRGB(0, 0, 0)
    canv.setFont('Helvetica-Bold', 14, leading=None)
    canv.drawCentredString(120, 730, "ITEMS")
    canv.drawCentredString(320, 730, "RATE")
    canv.drawCentredString(410, 730, "QTY")
    canv.drawCentredString(500, 730, "AMOUNT")
    canv.setFont('Helvetica', 8, leading=None)
    y_coordinate = 710
    chaska = 0
    length = len(description_of_items)
    for chaska in range(length):
        canv.drawCentredString(120, y_coordinate,description_of_items[chaska])
        canv.drawCentredString(320, y_coordinate, str(cost_of_items[chaska]))
        canv.drawCentredString(410, y_coordinate, str(qty[chaska]))
        canv.drawCentredString(500, y_coordinate, '$' + str(amount[chaska]))
        y_coordinate = y_coordinate - 15
    y_coordinate = y_coordinate - 25
    canv.line(310, y_coordinate, 580, y_coordinate)
    canv.setFont('Helvetica-Bold', 12, leading=None)
    canv.drawCentredString(410, y_coordinate-16, "Total")
    canv.drawCentredString(500, y_coordinate-16, '$' + str(cost))
    canv.setFillColorRGB(0,0,255)
    canv.setFont('Helvetica', 16, leading=None)
    canv.drawCentredString(55, y_coordinate-16, "Raised For:")
    canv.setFillColorRGB(0, 0, 0)
    P = Paragraph(raise_for, style)
    aW = 180
    aH = y_coordinate-46
    w, h = P.wrap(aW, aH)  # find required space
    if w <= aW and h <= aH:
        P.drawOn(canv, 12, aH)
        aH = aH - h  # reduce the available height
    canv.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


class RaiseInvoice(View):


    form_class = RaiseInvoiceForm
    template_name = 'invoiceapp/raise_invoice.html'
    #Invoiceformset = modelformset_factory(Invoice, fields=('description_of_items','quantity','cost'), extra=2)
    def get(self, request):
        if not request.user.is_authenticated():
            return render(request,'invoiceapp/login.html',{'message':'Login First'})
        form = self.form_class(None)
        #formset = self.Invoiceformset(queryset=Invoice.objects.none())
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
           description_of_items = []
           cost_of_items = []
           amount = []
           qty = []
           cost = 0
           for i in range(3):
               x = 'form-' + str(i) + '-description_of_items'
               y = 'form-' + str(i) + '-cost'
               z = 'form-' + str(i) + '-quantity'
               x = str(x)
               y = str(y)
               p = request.POST[x]
               q = request.POST[y]
               r = request.POST[z]

               if q!='' or r!='':
                   cost = int(cost) + (int(q) * int(r))
                   s = (int(q) * int(r))
                   cost_of_items.append(q)
                   amount.append(s)
                   description_of_items.append(p)
                   qty.append(r)

           client = form.cleaned_data['client']
           obg = Client.objects.get(organisation_name=client)

           subject = 'Invoice'
           message = form.cleaned_data['message']
           #raise_for = form.cleaned_data['raise_for']
           raise_for = obg.organisation_name + "," + obg.client_address
           currency = form.cleaned_data['currency']
        #   by = Company_credentials.objects.filter(user=request.user)
          # print(by)


           sender = request.user.email
           reciever = obg.email
           receivers = [reciever]

           pdf = generate_certificate(description_of_items,cost_of_items,amount,cost,qty,raise_for,request)
           msg = EmailMessage(subject, message, sender, receivers)
           msg.attach_file('my_pdf.pdf', pdf)
           raiseinvoice = form.save(commit=False)
           raiseinvoice.raise_for = obg.organisation_name
           raiseinvoice.user = request.user
           raiseinvoice.email_to = obg.email
           raiseinvoice.cost = cost
           x = Company_credentials.objects.get(user=request.user)
           raiseinvoice.raised_by =  str(x.company_name)
           raiseinvoice.client = client
           total_items = [int(x) for x in qty]
           raiseinvoice.quantity = sum(total_items)
           raiseinvoice.save()
           msg.send(fail_silently=True)

           return redirect('invoiceapp:index')
        return redirect('invoiceapp:raiseinvoice')




def Estimates(request):
    if not request.user.is_authenticated():
        return render(request,'invoiceapp/login.html',{'message':'Login First'})
    template_name = 'invoiceapp/estimates.html'
    all_invoices = Invoice.objects.filter(user=request.user).order_by('-pk')
    total = 0
    for invoice in all_invoices:
        total = total + invoice.cost
    return render(request,template_name,{'all_invoices':all_invoices,'amount':total})




def Changestatus(request,id):
    selected_invoice = Invoice.objects.get(pk=id)
    amount = request.POST['amount']
    amount = int(amount)
    cost = selected_invoice.cost
    if amount > cost:
        pass
    else:
        selected_invoice.cost = (cost) - amount
    selected_invoice.save()
    return redirect('invoiceapp:estimates')

def client(request):
    all_clients = Client.objects.filter(user=request.user)
    return render(request, 'invoiceapp/client.html', {'all_clients': all_clients})

class add_client(View):
    form_class = ClientForm
    template_name = 'invoiceapp/add_client.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form,})

    def post(self, request):
        form = self.form_class(request.POST or None, request.FILES or None)
        if not request.user.is_authenticated():
            return render(request, 'invoiceapp/login.html',{ 'message': 'Login First'})
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
        return redirect(reverse('invoiceapp:client'))



def deleteclient(request,pk):
    client = Client.objects.get(pk=pk)
    client.delete()
    return redirect(reverse('invoiceapp:client'))


def invoices_for_me(request):
    objects = Invoice.objects.filter(email_to=request.user.email).order_by('-pk')
    return render(request,'invoiceapp/invoices_for_me.html',{'objects':objects})

















