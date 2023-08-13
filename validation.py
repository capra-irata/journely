from re import match

def enforce_password(password,
                     min_characters=8,
                     req_lower=True,
                     req_upper=True,
                     req_digit=True,
                     req_symbol=True):
  """Enforces common password requirements for given password

  Returns True if password is acceptable, False otherwise.
  Current implementation of this function is simplistic as it does not reject
  unusual characters.

  TODO: Requires thorough testing.
  """

  # Ensure proper usage
  if not password:
    return False
  elif type(min_characters) != int or min_characters < 1:
    raise ValueError(
      'Argument "min_characters" of function "enforce_password" must be an int >= 1')
  elif type(req_lower) != bool:
    raise TypeError(
      'Argument "req_lower" of function "enforce_password" must be of type bool')
  elif type(req_upper) != bool:
    raise TypeError(
      'Argument "req_upper" of function "enforce_password" must be of type bool')
  elif type(req_digit) != bool:
    raise TypeError(
      'Argument "req_digit" of function "enforce_password" must be of type bool')
  elif type(req_symbol) != bool:
    raise TypeError(
      'Argument "req_symbol" of function "enforce_password" must be of type bool')

  # Final regular expression will be determined based on function's arguments

  # Regex that matches any string between 0 and {min_characters - 1} characters
  re_c = f'.{{0,{min_characters - 1}}}'

  re_l = ''
  if req_lower:
    # Match any characters that are not lowercase
    re_l = '|[^a-z]*'

  re_u = ''
  if req_upper:
    # Match any characters that are not uppercase
    re_u = '|[^A-Z]*'

  re_d = ''
  if req_digit:
    # Match any characters that are not digits
    re_d = '|[^\d]*'

  re_s = ''
  if req_symbol:
    # Match any characters that are not the symbols found on 1-8 on the keyboard
    re_s = '|[^!@#$%^&*]*'

  # Piece together the regex strings for our final expression. ^()$ ensures we
  # check each alternative delimited by | for the entire password
  regex = f'^({re_c}{re_l}{re_u}{re_d}{re_s})$'

  # If a match is found, the password is missing a requirement so return False
  return False if match(regex, password) else True