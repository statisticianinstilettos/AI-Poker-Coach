import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import getpass

def create_user():
    print("Create New User")
    print("--------------")
    username = input("Enter username: ")
    email = input("Enter email: ")
    name = input("Enter full name: ")
    password = getpass.getpass("Enter password: ")
    
    # Generate password hash
    hashed_password = stauth.Hasher([password]).generate()[0]
    
    # Load existing config
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Add new user
    if 'credentials' not in config:
        config['credentials'] = {'usernames': {}}
    
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': hashed_password
    }
    
    # Save updated config
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    print(f"\nUser {username} created successfully!")
    print("You can now log in to the application with these credentials.")

if __name__ == "__main__":
    create_user() 