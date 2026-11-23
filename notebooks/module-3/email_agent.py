from pydantic import BaseModel, Field
from datetime import datetime, timezone
from langchain.tools import tool

'''
Requirements:
- authenticate user
- read an email
- sends email with human-in-the-loop

Notes:
- Dummy functions are fine, no need to use actual email APIs
- Can store emails in a list or dictionary for simplicity
'''

# from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
# from langchain.messages import AIMessage, ToolCall, HumanMessage

# model = GenericFakeChatModel(messages=iter([
#     AIMessage(content="", tool_calls=[ToolCall(name="foo", args={"bar": "baz"}, id="call_1")]),
#     AIMessage(content="Some content, like 'bar'")
# ]))

# print(model.invoke("hello"))
# # AIMessage(content='', ..., tool_calls=[{'name': 'foo', 'args': {'bar': 'baz'}, 'id': 'call_1', 'type': 'tool_call'}])

# print(model.invoke("hello again!"))

### Authentication logic
class UserCredentials(BaseModel):
    username: str = Field(
        description="The username of the user."
    )
    password: str = Field(
        description="The password of the user."
    )

@tool
def authenticate_user(user_credentials: UserCredentials) -> bool:
    # TODO: rewrite to use abstractions to account for local (dummy) credentials and real credentials
    """Authenticate the user"""

    # Dummy authentication logic
    if user_credentials.username == "user" and user_credentials.password == "password":
        return True
    return False

# Tests that call functions with the @tool decorator need to be called with the StructuredTool.func attribute, see here: https://reference.langchain.com/python/langchain-core/tools/structured/StructuredTool/funcs
def test_authenticate_user_returns_true_with_correct_credentials():
    user_credentials = UserCredentials(username="user", password="password")

    result = authenticate_user.func(user_credentials)
    assert result == True
    assert isinstance(user_credentials, UserCredentials)

### Email reading logic
'''
Email would be stored in a dictionary
- The key would be the email id and the value would be the email content
- The value would need to adhere to a specific pydantic model
'''

class EmailData(BaseModel):
    sender: str = Field(
            description="The email of the sender"
        )
    content: str = Field(
                description="The content of the email"
        )
    timestamp: datetime = Field(
                description="Timestamp of when the email was received"
    )

@tool
def read_email(emails: dict, email_id: str) -> dict:
    # TODO: rewrite to use abstractions to account for local (dummy) email data and real data

    """Return the email"""

    return emails[email_id]

def test_existing_email_id_returns_email_content():
    test_emails = {
        "1": EmailData(sender="some.sender@example.com", content="Hi, this is some test content.", timestamp=datetime.now(timezone.utc).isoformat())
    }
    email_id = "1"

    result = read_email.func(test_emails, email_id)

    assert isinstance(result, EmailData)
    assert result.content == "Hi, this is some test content."



### For later use with agent
# emails = {
#     "1": EmailData(sender="some.sender@example.com", content="Hi Alex, how's the langchain academy going? Best, Some Sender.", timestamp=datetime.now(timezone.utc).isoformat())
# }