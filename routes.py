from flask import render_template, request , send_from_directory
from models import *
from app import app 
import os
import re


#-----------------------------------------------------------------

'''

        # Admin Routes 


'''

#------------------------------------------------------------------
# Main landing page 
@app.route('/')
def hello():
    return render_template('index.html')

#------------------------------------------------------------------
#helper function for the stats route to get the matplotlib a new thread to do its work
            
# Admin stats route 
@app.route("/adminStats")
def adminStats():
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use("Agg")

    book_requests = BookRequests.query.all()
    try:
        book_requests = [{"id":book.id, "userId":book.userId, "bookId":book.bookId, "granted":book.granted, "time":book.time} for book in book_requests]
        df = pd.DataFrame(book_requests)
        plt.hist( df["bookId"])
        plt.xlabel('BookId')
        plt.ylabel('Requests')
        plt.title('Books with most Requests')
        

        plt.savefig('./static/uploads/bookRequests.png')
        plt.clf()
        # Not granted vs granted requests
        granted = len(df[df["granted"]==True])
        not_granted = len(df[df["granted"]==False])
        
        categories  = ["Not granted", "Granted"]
        plt.pie( [not_granted, granted], labels=categories,autopct='%1.1f%%' ,colors=["blue", 'orange'])
        plt.title("Comparison of Request Not Granted vs Granted")
        plt.savefig('./static/uploads/pieAdmin.png')
        plt.clf()
        
        # request by user
        plt.hist(df["userId"])
        plt.title("Number of Request individually by Users")
        plt.xlabel("UserId")
        plt.ylabel("Number of Book Requests")
        plt.savefig('./static/uploads/userRequests.png')
        plt.clf()
    except :
        return "Not enough user data to Generate Graphs"
    return render_template("stats.html")


#---------------------------------------------------------------
# Admin logout route
@app.route("/adminLogout")
def adminLogout():
    return render_template("index.html")

#---------------------------------------------------------------
# Admin home route
@app.route('/adminHome')
def adminHome():
    sections = Section.query.all()
    return render_template('adminHome.html', sections=sections)

#--------------------------------------------------------------
# helper function for request route to extract the duration of the request
def extract(tf):
    pattern = r'(\d+)(day|week|month)'
    m = re.findall(pattern, tf)
    number = int(m[0][0])
    duration = m[0][1]
    return number, duration

# approve request route
@app.route("/approveRequest/<int:bookRequestId>")
def approveRequest(bookRequestId):
    
    from datetime import datetime, timedelta
    bookRequest = BookRequests.query.filter_by(id=bookRequestId).first()
    bookRequest.granted = True
    bookRequest.requestAcceptedTF = int(datetime.now().timestamp())
    number,  duration = extract(bookRequest.time)
    revokeTime = None
    if duration == "day":
        revokeTime =   datetime.now()+ timedelta(days=number)
    elif duration == "week":
        revokeTime = datetime.now()+ timedelta(weeks=number)
    else:
        revokeTime = datetime.now()+timedelta(months= number)

    revokeTime = int(revokeTime.timestamp(  ))
    bookRequest.requestRevokeTF = revokeTime    
    db.session.commit()
    bookRequests = BookRequests.query.all()
    return render_template("requestsByUsers.html", bookRequests = bookRequests)

#--------------------------------------------------------------
# discard request route
@app.route("/discardRequest/<int:bookRequestId>")
def discardRequest(bookRequestId):
    bookRequest = BookRequests.query.filter_by(id=bookRequestId).first()
    db.session.delete(bookRequest)
    db.session.commit()
    bookRequests = BookRequests.query.all()
    return render_template("requestsByUsers.html", bookRequests = bookRequests)
#---------------------------------------------------------------
# Admin login route
@app.route("/adminLogin", methods=["GET", "POST"])
def adminLogin():
    if request.method == "GET":

        return render_template("adminLogin.html")
    if request.method == "POST":
        username = request.form["username"]
        admin= Admin.query.filter_by(username = username).first()
        if (not admin):
            return ("Your are not registered , please register first")
        password = request.form["password"]
        admin = Admin.query.filter_by(username = username , password=password).first()
        sections = Section.query.all()
        if (admin):
            if(sections):
                return render_template("adminHome.html" , sections=sections)
            else:
                return render_template("adminHome.html")
        else:
            return render_template("error.html")

@app.route("/adminRegister" , methods=["GET","POST"])
def adminRegister():
    if request.method=="GET":
        return render_template("adminRegister.html")        
    if request.method=="POST":
        username = request.form["username"]
       
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).first()
        if (admin):
            return "Admin already exists"
        admin = Admin(username=username , password = password)
        db.session.add(admin)
        db.session.commit()
        sections = Section.query.all()
        
        if(sections):
            return render_template("adminHome.html" , sections=sections)
        else:
            return render_template("adminHome.html")
    else:
        return render_template("error.html")
#-----------------------------------------------
# add sections for the admin 
@app.route("/addSection", methods=["GET","POST"])
def addSection():
    if request.method=="GET":
        return render_template("addSection.html")
    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        desc = request.form["desc"]
        section = Section(title=title, date=date , desc = desc)
        db.session.add(section)
        db.session.commit()
        sections = Section.query.all()
        return render_template("adminHome.html",sections=sections)
    return "Section can't be added"
#--------------------------------------------------------------
# add new book route
@app.route("/addBook/<string:section>/<int:sectionId>", methods=["GET", "POST"])
def addBook(section , sectionId ):
    if request.method == "GET":
        books = Book.query.filter_by(section_id = sectionId).all()

        return render_template("addNewBook.html", section =section , sectionId = sectionId , books=books)
    if request.method == "POST":
        file = request.files["file"]
        title  = request.form["title"]
        author = request.form["author"]
        content = request.form["content"]
        price = request.form["price"]
        bookCover = request.files["bookCover"]

        book = Book(title=title, author=author , content = content , section_id = sectionId, book_section=section, price=price)
        try:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], title+".pdf"))
            bookCover.save(os.path.join(app.config['UPLOAD_FOLDER'], title+".jpg"))
        except:
            return "SOme error occured"


        db.session.add(book)
        db.session.commit()
        books = Book.query.filter_by(section_id = sectionId).all()

        return render_template("addNewBook.html", section =section , sectionId = sectionId , books=books)

#--------------------------------------------------------------------
# requests by the user
@app.route("/requestsByUsers")
def requestsByUsers():
    bookRequests = BookRequests.query.all()
    return render_template("requestsByUsers.html", bookRequests = bookRequests)


#--------------------------------------------------------------------
# delete section route
@app.route("/deleteSection" , methods=["GET", "POST"])
def deleteSection():
    if request.method == "GET":
        
        sections = Section.query.all()
        return render_template("deleteSection.html", sections=sections)
    if request.method == "POST":
        sectionId = request.form["section"]
        section = Section.query.filter_by(id=sectionId).first()
        books = section.books
        for book in books:
            db.session.delete(book)
            db.session.commit()
        db.session.delete(section)
        db.session.commit()
        return f'{section.title} Section deleted'
    else:
        return "Some Error Occured"
    
#----------------------------------------------------------------------------
# delete book route
@app.route("/deleteBook/<int:bookId>/<int:sectionId>")
def deleteBook(bookId, sectionId):
    print(bookId, sectionId)
    book = Book.query.filter_by(id= bookId).first()
    section = Section.query.filter_by(id = sectionId).first()
    book_requests = BookRequests.query.filter_by(bookId=bookId).all()
    if book_requests:
        for i in book_requests:
            db.session.delete(i)
            db.session.commit()
    feedback = book.feedback
    if feedback != []:
        for  i in feedback:
            db.session.delete(i)
            db.session.commit()
    file = os.path.join(app.config['UPLOAD_FOLDER'], book.title+".pdf")
    if os.path.exists(file):
        os.remove(file)
    bookCover = os.path.join(app.config["UPLOAD_FOLDER"], book.title+".jpg")
    if os.path.exists(bookCover):
        os.remove(bookCover)

    db.session.delete(book)
    db.session.commit()
    books = section.books
    return  render_template("addNewBook.html", section =section.title , sectionId = sectionId , books=books)
    
#-------------------------------------------------------------------------



#-----------------------------------------------------------------------------
    '''
    -------------------------------------------------

    User Routes are defined here below

    -------------------------------------------------
    
    '''

#------------------------------------------------------------------------------
    
# user home page route

# user login route 
@app.route("/userLogin", methods=["GET", "POST"])
def userLogin():
    if request.method == "GET":
        return render_template("user/login.html")
    if request.method == "POST":
        username = request.form["username"]
        user = User.query.filter_by(username = username).first()
        if (not user):
            return ("Your are not registered , please register first")
        password = request.form["password"]
        user = User.query.filter_by(username = username , password=password).first()
        sections  = Section.query.all()
        # Now here there will be the check for the books if any of the book has exceeded its issue date and it will revoked immediately

        #--------------------------------------------------------------
        if (user):
            user_requested_books = user.books_requested
            if user_requested_books:
                
                for i in user_requested_books:
                    if i.granted == True:
                        if i.requestAcceptedTF > i.requestRevokeTF:
                            i.granted = False
            
            return render_template("user/home.html" , sections=sections, user=user )
        else:
            return render_template("error.html")
        

#--------------------------------------------------------------
# user register route
@app.route("/userRegister", methods=["GET", "POST"])
def userRegister():
    if request.method == "GET":
        return render_template("user/register.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if(user):
            return "User already exists"
        user = User(username=username , password = password)
        db.session.add(user)
        db.session.commit()
        return render_template("user/login.html")
    return "User can't be registered"

#--------------------------------------------------------------
# user books
@app.route("/userBooks/<int:userId>", methods=["GET", "POST"])
def userBooks(userId):
    if request.method == "GET":
        user = User.query.filter_by(id=userId).first()
        if (user):
            return render_template("user/userBooks.html", user=user)
        else:
            "There is a bug from our side"

#--------------------------------------------------------------
# request book 
@app.route("/requestBook/<int:userId>/<int:bookId>/<string:status>/<string:location>")
def requestBook(userId , bookId, status, location):

    if status == "request":
        books_requested_by_user = BookRequests.query.filter_by(userId=userId).all()
        if books_requested_by_user:
            if len(books_requested_by_user) >= 5:
             return    render_template("user/error.html" , userId = userId , errorMessage = "Sorry, you can't request more than 5 Books")
        time = request.args.get("time" , "")
        if time=="":
            time = "1"
        timeUnit = request.args.get("timeUnit", "")

        book_request = BookRequests(userId=userId , bookId=bookId , granted=False, time=time+timeUnit)
        db.session.add(book_request)
        db.session.commit()
    else:
        book_request = BookRequests.query.filter_by(userId=userId, bookId=bookId).first()
        db.session.delete(book_request)
        db.session.commit()
    book = Book.query.filter_by(id=bookId).first()
    books = book.section.books

    user = User.query.filter_by(id=userId).first()
    requestedBooks = user.books_requested
    requestBooksId = []
    for i in requestedBooks:
        requestBooksId.append(i.bookId)
    
    
    if location == "section":
        return render_template("user/sectionView.html",user=user,section=book.section, books=books, requestedBooksId = requestBooksId)
    else:
        return render_template("user/userBooks.html", user=user)
               
#--------------------------------------------------------------
# stats route 
@app.route("/userStats/<int:userId>")
def statsRoute(userId):
    import pandas as pd
    import matplotlib
    import matplotlib.pyplot as plt 
    matplotlib.use("Agg")

    book_requests = BookRequests.query.all()
    book_requests = [{"id":book.id, "userId":book.userId, "bookId":book.bookId, "granted":book.granted, "time":book.time} for book in book_requests]
    df = pd.DataFrame(book_requests)
    try :
        userData = df.loc[df["userId"]==userId]
        totalRequests = len(userData)
        grantedRequests = len(userData.loc[userData["granted"]==True])
        plt.pie([totalRequests, grantedRequests], labels=["Total Requests", "Granted Requests"],autopct="%1.1f%%", colors=["Turquoise", "Coral"])
        plt.title("Total Requests vs Granted Requests")
        plt.savefig('./static/uploads/userPie'+str(userId)+'.png')
        plt.clf()
    except Exception as e:
        return("Not enough user data to Generate Graphs")
    

    return render_template("user/stats.html" , user=User.query.filter_by(id=userId).first())
            
#--------------------------------------------------------------
# user logout route
@app.route("/userLogout")
def userLogout():
    return render_template("index.html")

#--------------------------------------------------------------
# user home page
@app.route("/books/<int:userId>")
def userHome(userId):
    user = User.query.filter_by(id=userId).first()
    sections  = Section.query.all()
    return render_template("user/home.html" , user = user , sections = sections)


#-----------------------------------------------------------------
# Section to be viewed
@app.route("/<int:userId>/<int:sectionId>")
def sectionView(sectionId , userId):
    section = Section.query.filter_by(id=sectionId).first()
    user = User.query.filter_by(id=userId).first()
    books = section.books
    requestedBooks = user.books_requested
    requestedBooksId = []
    for i in requestedBooks:
        requestedBooksId.append(i.bookId)
    
    return render_template("user/sectionView.html", section=section, books=books, user=user , requestedBooksId=requestedBooksId)


@app.route("/writeComment/<int:bookId>/<int:userId>/<int:sectionId>" , methods=["GET", "POST"])
def writeComment(bookId, userId, sectionId):
    if request.method == "POST":
        comment = request.form["Comment"]
        
        user = User.query.filter_by(id=userId).first()
        section = Section.query.filter_by(id=sectionId).first()

        books = section.books

        feedback = Feedback(book_id=bookId, feedback=comment)
        db.session.add(feedback)
        db.session.commit()
        return render_template("user/sectionView.html", section = section, books=books, user=user )



@app.route("/buyBook/<int:bookId>")
def buyBook(bookId):
    book = Book.query.filter_by(id=bookId).first()
    return render_template("user/paymentPage.html", book = book)
@app.route("/downloadBook/<int:bookId>")
def downloadBook(bookId):
    book = Book.query.filter_by(id = bookId).first()
    book_title = book.title+".pdf"
    return send_from_directory(app.config['UPLOAD_FOLDER'], book_title, as_attachment=True)

#--------------------------------------------------------------
# viewTheBook
@app.route("/viewTheBook/<int:bookId>")
def viewTheBook(bookId):
    book = Book.query.filter_by(id=bookId).first()
    book_title = book.title
    return render_template("user/readBook.html",book_title = book_title)

#-----------------------------------------------------------------

'''

        # Universal Routes


'''

#------------------------------------------------------------------

@app.route("/search/<int:userId>/<string:role>", methods = ["GET", "POST"])
def search(userId, role):
    if role == "user":
        user = User.query.filter_by(id=userId).first()
        requestedBooks = user.books_requested
        requestedBooksId = []
        for i in requestedBooks:
            requestedBooksId.append(i.bookId)
        type = request.form["searchType"]
        
        if (type == "book" ) or (type == "author"):
            if type == "book":
                book = request.form["input"]
                book = Book.query.filter_by(title=book).first()
                    
                return render_template("user/searchBookResult.html",user=user,books=[book], requestedBooksId=requestedBooksId,type="bookSearch")
            else:
                author = request.form["input"]
                book = Book.query.filter_by(author=author)
                return render_template("user/searchBookResult.html",user=user,books=book, requestedBooksId=requestedBooksId)
        if type == "section":
            section = request.form["input"]
            section = Section.query.filter_by(title=section).first()
            

            return render_template("user/searchResult.html", type= "section", section=section,user=user)
    else:
            type = request.form["searchType"]
            if type == "section":
                section = request.form["input"]
                section = Section.query.filter_by(title=section).first()
                return render_template("adminSearchSectionResult.html", section = section )
            else:
                if type=="book" or type=="author":
                    if type == "book":
                        book = request.form["input"]
                        book = Book.query.filter_by(title=book).first()
                        return render_template("adminSearchBookResult.html", books = [book])
                    else:
                        author = request.form["input"]
                        book = Book.query.filter_by(author=author).all()
                        return render_template("adminSearchBookResult.html", books = book)




