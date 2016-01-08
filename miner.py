from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError

from py2neo import Graph    

import time

graph = Graph()
cypher = graph.cypher

graph.schema.create_uniqueness_constraint("USER", "id")
graph.schema.create_uniqueness_constraint("USER", "username")

CLIENT_ID = ""
CLIENT_SECRET = ""

ROOT_USER = "madhavgharmalkar"

DEPTH = 2
DELAY_OVERRIDE = 10     # In seconds

#   Create our Instagram API client
    
print("Creating client...")
api = InstagramAPI(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)


def cypher_user_push(tx, a, b) ->None:
    """USER A FOLLOWS B"""
    tx.append("""  MERGE (a:USER {username:{auser}, id:{aid}})
                        MERGE (b:USER {username:{buser}, id:{bid}})
                        MERGE a-[:FOLLOWS]->b""", auser = a.username, aid = a.id, buser = b.username, bid = b.id)

def user_follows_mine(user: InstagramAPI.user, depth: int) -> None:

    tx = graph.cypher.begin()

    if depth == 0:
        return

    #   Get the current users' follows
    try:
        print("Finding {}'s follows".format(user.username))
        followers, next_ = api.user_follows(user.id)

        end = time.time() + DELAY_OVERRIDE

        while next_ and (time.time() < end):
            more_followers, next_ = api.user_follows(user.id, with_next_url=next_)
            followers.extend(more_followers)
    except InstagramAPIError as e:
        if e.status_code == 400:
            print("{} is priave :(".format(user.username))
        elif e.status_code == 429:
            print("The api limit has been reached for {}".format(user.username))
        else:
            print("Error {}".format(e))
        return
    
    # Creat Neo4j Relationships

    for u in followers:
        cypher_user_push(tx, user, u)

    tx.commit()

    if depth - 1 == 0:
        return

    # Recursive Call
    for u in followers:
        user_follows_mine(u, depth-1)
    return

def user_followers_mine(user: InstagramAPI.user, depth: int) -> None:

    tx = graph.cypher.begin()

    if depth == 0:
        return

    #   Get the current users' followers
    try:
        print("Finding {}'s followers".format(user.username))
        followers, next_ = api.user_followed_by(user.id)

        end = time.time() + DELAY_OVERRIDE

        while next_ and (time.time() < end):
            more_followers, next_ = api.user_followed_by(user.id, with_next_url=next_)
            followers.extend(more_followers)
    except InstagramAPIError as e:
        if e.status_code == 400:
            print("{} is priave :(".format(user.username))
        elif e.status_code == 429:
            print("The api limit has been reached for {}".format(user.username))
        else:
            print("Error {}".format(e))
        return
    
    # Creat Neo4j Relationships
    for u in followers:
        cypher_user_push(tx, u, user)

    tx.commit()

    if depth - 1 == 0:
        return

    # Recursive Call
    for u in followers:
        user_followers_mine(u, depth-1)
    return


def main() -> None:

    # Get the root user's ID
    print("Fetching {}'s informatiom".format(ROOT_USER))
    userSearchResults = api.user_search(q = ROOT_USER)
    
    if len(userSearchResults) == 0:
        print("Root user not found / invalid user")
        return

    # Get the best match user: 
    user = userSearchResults[0]

    # user_followers_mine(user, DEPTH)
    user_follows_mine(user, DEPTH)

    tx.commit()

    return



if __name__ == "__main__":
    main()

 
