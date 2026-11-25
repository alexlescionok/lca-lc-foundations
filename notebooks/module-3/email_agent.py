from pydantic import BaseModel, Field
from datetime import datetime, timezone
from langchain.tools import tool
from langchain_core.tools import StructuredTool
import json
import pytest
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.messages import HumanMessage

load_dotenv()


'''
Requirements:
- authenticate user
- read an email
- sends email with human-in-the-loop

So the flow would be:
1. Authenticate the session.
2. If session is authenticated (True), call the read email function. If False, return permission error.
3. Draft email response and present it to the user.
4. User confirms if they are happy or if edits are required.

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

# ### Authentication logic
# class UserCredentials(BaseModel):
#     username: str = Field(
#         description="The username of the user."
#     )
#     password: str = Field(
#         description="The password of the user."
#     )


class UserCredentials(BaseModel):
    # TODO, add further validation here on the value of the UserCredentials, e.g. must be a JSON string with username/password, or PAT starting with a specific prefix.
    credentials: str = Field(
        description="The credentials string of the user. For example, a personal access token, or a username/password combination encoded as JSON."
    )

class AuthenticationInterface(ABC):
    """Interface for Authenticating users before they access emails."""

    @abstractmethod
    def authenticate_user(self, credentials: UserCredentials) -> bool:
        """Authenticate user using the provided credentials."""

class UsernamePasswordAuthentication(AuthenticationInterface):
    def authenticate_user(self, credentials: UserCredentials) -> bool:
        """Authenticate user using the provided credentials."""
        data = json.loads(credentials)
        username, password = data["username"], data["password"]

        if username == "username" and password == "password":
            return True
        return False

class Session:
    def __init__(self, authentication_result: bool = False) -> bool:
        self.authenticated = authentication_result

def make_tools(session: Session, mail_client = None):
    @tool
    def read_emails() -> str:
        """Read latest email."""
        if not session.authenticated:
            raise PermissionError("Not authenticated.")

        # TODO: replace with actual email reading logic via the mail_client argument.
        return "successfully read emails. Here is the last email: 'Hi Alex, it's been a while! Hope you're keeping well. Best, LangChain.'"#mail_client.fetch(max_results)

    return [read_emails]

def get_tool(tools: list, tool_name: str) -> StructuredTool:
    tool = next((t for t in tools if t.name == tool_name), None)
    if tool == None:
        raise KeyError(f"No tool found with name: {tool_name}")
    return tool

def test_authentication_implementations():
    instance = UsernamePasswordAuthentication()
    assert issubclass(UsernamePasswordAuthentication, AuthenticationInterface)
    assert isinstance(instance, AuthenticationInterface)

# Tests that call functions with the @tool decorator need to be called with the StructuredTool.func attribute or StructuredTool.invoke method (inherited from BaseTool)
# Using .invoke({}) validates a larger part of the tool code (e.g. it includes Pydantic schema validation) and runs the tool the way the agent would run it. Whereas .func() runs just the function's logic, proving that the function works, but not necessarily that the function will work as a tool called by an agent.
# see here: https://reference.langchain.com/python/langchain-core/tools/structured/StructuredTool
def test_successful_username_password_authentication():
    json_credentials_string = '{"username": "username", "password": "password"}'
    user_credentials = UserCredentials(credentials=json_credentials_string)
    
    result = UsernamePasswordAuthentication().authenticate_user(user_credentials.credentials)

    assert result == True

def test_session_is_false_by_default():
    session = Session()

    assert session.authenticated == False

def test_session_is_true_once_authenticated():
    json_credentials_string = '{"username": "username", "password": "password"}'
    user_credentials = UserCredentials(credentials=json_credentials_string)
    
    authentication_result = UsernamePasswordAuthentication().authenticate_user(user_credentials.credentials)
    print(f"Authentication result: {authentication_result}")
    session = Session(authentication_result)

    assert session.authenticated == True

def test_get_tool_returns_existing_tool():
    session = Session()
    session.authenticated = True
    tool_name = "read_emails"
    
    tools = make_tools(session)
    result = get_tool(tools, tool_name)
    
    assert isinstance(result, StructuredTool)

def test_get_tool_returns_key_error_when_no_tool_is_found():
    session = Session()
    session.authenticated = True
    tool_name = "fake_tool"
    
    tools = make_tools(session)
    with pytest.raises(KeyError, match=f"No tool found with name: {tool_name}"):
        get_tool(tools, tool_name)
    

def test_read_emails_raises_permission_error_without_authentication():
    session = Session()
    tools = make_tools(session)
    
    tool_name = "read_emails"
    read_emails = get_tool(tools, tool_name)
    with pytest.raises(PermissionError, match="Not authenticated."):
        read_emails.invoke({})

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

# def test_email_is_of_instance_dict_email_data():
#     test_emails = {
#             "1": EmailData(sender="some.sender@example.com", content="Hi, this is some test content.", timestamp=datetime.now(timezone.utc).isoformat())
#         }
    
#     result = read_email.func(test_emails, email_id)
#     assert isinstance(result, DictEmailData)

### For later use with agent
# emails = {
#     "1": EmailData(sender="some.sender@example.com", content="Hi Alex, how's the langchain academy going? Best, Some Sender.", timestamp=datetime.now(timezone.utc).isoformat())
# }



### Read emails
### TODO: write unit tests to assert that the agent calls read_emails tool.

# session = Session()
# session.authenticated = True
# tools = make_tools(session)

# agent = create_agent(
#     model="ollama:gemma4",
#     tools=tools
# )

# response = agent.invoke(
#     {"messages": [HumanMessage(content=f"What does my latest email say?")]}
# )

# print(response["messages"][-1].content)