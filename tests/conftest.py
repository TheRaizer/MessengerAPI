"""Shared data used during tests"""

valid_passwords = [
    "Password231",
    "aValidpassword2",
    "eloWor1d",
    "2_password_D-*9)",
    ')(@#&*"@#(*@GOod22',
]

invalid_passwords = [
    "aBC4567",
    "not_upper_case2",
    "ONLY UPPER12 CASE",
    "noNumbers",
    "22123233",
]

valid_usernames = [
    "valid_username.23",
    "vAli",
    "hello.world",
    "223221",
    "USERNAME",
    "username",
    "hie",
]

invalid_usernames = [
    "_invalid",
    "invalid_",
    "invalid__user",
    "hi_.there",
    "some._user",
    "boop..bop",
    "bing...bang",
    "also__.invalid",
    "has*invalid)()@#characters",
    "this_username_is_far_too_long_to_be_valid",
    "hi",
]

valid_emails = [
    "email@email.com",
    "something@email.com",
    "my.ownsite@ourearth.org",
    "aperson@gmail.com",
]

invalid_emails = ["@email.com", "cool.cool", "not an email", "google.email@com"]
