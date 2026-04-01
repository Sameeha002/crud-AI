# test_chinook.py
import sys
sys.path.append("crudAI-backend")

from multiAgents.tools.chinook_db import get_session, get_classes

session = get_session()
classes = get_classes()
Customer = classes.Customer

result = session.query(Customer).all()
for c in result[:5]:
    print(c.CustomerId, c.Email)