from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Auction_Listing, Biddings, Comments, Watchlist

# Active Listing Page
def index(request):
    return render(request, "auctions/index.html", {
        "auction_listings": Auction_Listing.objects.all()
    })

# Login
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

# Logout
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

# Register
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

# Create Listing
@login_required
def create_listing(request):
    if request.method == "POST":
        name = request.POST["title"]
        item_description = request.POST["description"]
        img = request.POST["img"]
        category = request.POST["category"]

        
        start = request.POST["sbid"]
        if start == '':
            return render(request, "auctions/create.html", {
                "message": "No starting bid given"
            })
        else:
            startb = int(start)
        
        # Giving error if user has no entered name
        if not name:
            return render(request, "auctions/create.html", {
                    "message": "No title given"
                }) 

        # Giving error if user has no entered description
        if not item_description:
            return render(request, "auctions/create.html", {
                    "message": "No description given"
                })
        
        # If no image url is given then assigning image url as "No Image" url
        if not img:
            img = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png"

        # Assigning category as NA if user has not entered any category for item
        if not category:
            category = "NA"

        user_id = request.session['_auth_user_id']
        username = User.objects.get(id=user_id)

        # Inserting the data in Auction_Listing Model
        listing = Auction_Listing.objects.create(creator= username, title=name, description=item_description, starting_bid=startb, updated_bid=0, image=img, category=category, closed=False)
        listing.save()

    return render(request, "auctions/create.html")

# Watchlist
@login_required
def watchlist(request):
    user = User.objects.get(username=request.user.username)

    return render(request, "auctions/watchlist.html", {
        "watchlists": Watchlist.objects.all(),
        "user": user
    })

# Categories
@login_required
def categories(request):
    categories = Auction_Listing.objects.values_list("category", flat=True).distinct()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

# All of the Listings
def listings(request, item_id):
    items = Auction_Listing.objects.get(id=item_id)
    creator = items.creator_id
    winner_id = Biddings.objects.filter(item=items).values_list("bidder", flat=True).order_by("-bids").first()
    
    # Getting Username
    try:
        username = User.objects.get(username=request.user.username)
    except:
        username = None

    # If submitting bid or commenting
    if request.method == 'POST':        
        if items.starting_bid > items.updated_bid:
            current = items.starting_bid
        else:
            current = items.updated_bid
        
        # Watchlist
        if request.POST.get("rm", False):
            watchlisted = False
            usern = User.objects.values_list("id", flat=True).get(username=username)
            # Removing item from watchlisting if it was already added
            if usern in list(Watchlist.objects.filter(user=username, listing=items).values_list("user", flat=True)) and item_id in list(Watchlist.objects.filter(user=username, listing=items).values_list("listing", flat=True)):
                Watchlist.objects.filter(user= username, listing= items).update(is_watchlisted=watchlisted)
            return render(request, "auctions/listing.html", {
                "item": items,
                "creator": User.objects.get(id=creator),
                "user": username,
                "watchlist": list(Watchlist.objects.filter(user=username, listing=items).values_list("is_watchlisted", flat=True)),
                "comments": Comments.objects.all(),
                "closed": "Item has been closed for bidding",
                "closing": items.closed,
                "winner": User.objects.filter(id=winner_id).first()
            })

        elif request.POST.get("add", False):
            watchlisted = True
            usern = User.objects.values_list("id", flat=True).get(username=username)
            # Watchlisting Item
            if usern not in list(Watchlist.objects.values_list("user", flat=True)) and item_id not in list(Watchlist.objects.values_list("listing", flat=True)):
                Watchlist.objects.create(user= username, listing= items, is_watchlisted=watchlisted)
            # If Item already watchlisted then deleting it
            else:
                Watchlist.objects.filter(user= username, listing= items).delete()
                Watchlist.objects.create(user= username, listing= items, is_watchlisted=watchlisted)
            return render(request, "auctions/listing.html", {
                "item": items,
                "creator": User.objects.get(id=creator),
                "user": username,
                "watchlist": list(Watchlist.objects.values_list("is_watchlisted", flat=True)),
                "comments": Comments.objects.all(),
                "closed": "Item has been closed for bidding",
                "closing": items.closed,
                "winner": User.objects.filter(id=winner_id).first()
            })
            
        # Bidding
        if request.POST.get("bid", False) or request.POST.get("bid", False) == "":
            if request.POST.get("bid", False):
                try:
                    bid = int(request.POST["bid"])
                except:
                    bid = 0

                # Giving Error if bid made by user is below or equal to current price
                if bid < current or bid == current:
                    return render(request, "auctions/listing.html", {
                        "item": items,
                        "creator": User.objects.get(id=creator),
                        "message": "Bid should be higher than current price",
                        "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
                        "comments": Comments.objects.all(),
                        "winner": User.objects.filter(id=winner_id).first()
                })
            
                # Saving the new bid to database
                if bid is not None:
                    bidding = Biddings.objects.create(bidder=username, item= items, bids=bid)
                    Auction_Listing.objects.filter(title=items).update(updated_bid=bid)
                    bidding.save()
                    return render(request, "auctions/listing.html", {
                        "item": items,
                        "creator": User.objects.get(id=creator),
                        "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
                        "comments": Comments.objects.all(),
                        "winner": User.objects.filter(id=winner_id).first()
                    })

            # Giving Error if user has submitted empty value
            elif request.POST.get("bid", False) == "":
                return render(request, "auctions/listing.html", {
                        "item": items,
                        "creator": User.objects.get(id=creator),
                        "message": "Empty value",
                        "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
                        "comments": Comments.objects.all(),
                        "winner": User.objects.filter(id=winner_id).first()
                })

        # Comment
        if request.POST.get("comment", False) or request.POST.get("comment", False) == "":
            if request.POST.get("comment", False):
                comment = request.POST["comment"]
                
                # Saving the comment in database
                if comment is not None:
                    comments = Comments.objects.create(commentor=username, comment=comment, item_name=items)
                    comments.save()
            
            # Giving Error if user has not submitted any comment
            elif request.POST.get("comment", False) == "":
                return render(request, "auctions/listing.html", {
                        "item": items,
                        "creator": User.objects.get(id=creator),
                        "message2": "Dont leave comment empty",
                        "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
                        "comments": Comments.objects.all(),
                        "closing": items.closed,
                        "winner": User.objects.filter(id=winner_id).first()
                })

        # Closed Page
        if request.POST.get("close", False):
            Auction_Listing.objects.filter(title=items).update(closed=True)
            return render(request, "auctions/listing.html", {
                "item": items,
                "creator": User.objects.get(id=creator),
                "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
                "closed": "Item has been closed for bidding",
                "comments": Comments.objects.all(),
                "closing": items.closed,
                "winner": User.objects.filter(id=winner_id).first()
            })

    return render(request, "auctions/listing.html", {
        "item": items,
        "creator": User.objects.get(id=creator),
        "user": username,
        "watchlist": list(Watchlist.objects.filter(user= username, listing= items).values_list("is_watchlisted", flat=True)),
        "comments": Comments.objects.all(),
        "closed": "Item has been closed for bidding",
        "closing": items.closed,
        "winner": User.objects.filter(id=winner_id).first()
    })

# Particular Category 
def category(request, category):
    if Auction_Listing.objects.filter(category=category):
        cat = Auction_Listing.objects.filter(category=category)
    else:
        cat = None

    return render(request, "auctions/category.html", {
        "auction_listings": cat,
        "not_category": category
    })
