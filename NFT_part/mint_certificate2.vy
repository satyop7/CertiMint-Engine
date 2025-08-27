# pragma version ^0.4.1

from snekmate.tokens import erc721
from snekmate.auth import ownable as ow

initializes: ow
initializes: erc721[ownable := ow]

exports: (
    erc721.owner,
    erc721.balanceOf,
    erc721.ownerOf,
    erc721.getApproved,
    erc721.approve,
    erc721.setApprovalForAll,
    erc721.transferFrom,
    erc721.safeTransferFrom,
    # erc721.tokenURI, 
    erc721.totalSupply,
    erc721.tokenByIndex,
    erc721.tokenOfOwnerByIndex,
    erc721.burn,
    # erc721.safe_mint, 
    # erc721.set_minter,
    erc721.permit,
    erc721.DOMAIN_SEPARATOR,
    erc721.transfer_ownership,
    erc721.renounce_ownership,
    erc721.name,
    erc721.symbol,
    erc721.isApprovedForAll,
    erc721.is_minter,
    erc721.nonces,
)

# ------------------------------------------------------------------
#                             EVENTS
# ------------------------------------------------------------------
event CreatedNFT:
    tokenId: indexed(uint256)
    to: indexed(address)
    imageData: String[2700]
    subject: String[200]
    course: String[200]

# ------------------------------------------------------------------
#                        STATE VARIABLES
# ------------------------------------------------------------------
# Constants & Immutables
JSON_BASE_URI_SIZE: constant(uint256) = 29
IMG_BASE_URI_SIZE: constant(uint256) = 26
NAME: constant(String[15]) = "Certificate NFT"
SYMBOL: constant(String[4]) = "CNFT"
EIP_712_VERSION: constant(String[1]) = "1"
JSON_BASE_URI: constant(
    String[JSON_BASE_URI_SIZE]
) = "data:application/json;base64,"
IMG_BASE_URI: constant(String[IMG_BASE_URI_SIZE]) = "data:image/svg+xml;base64,"
FINAL_STRING_SIZE: constant(uint256) = 5000


# Contract storage
image_data: public(HashMap[uint256, String[2700]])
subjects: public(HashMap[uint256, String[200]])
courses: public(HashMap[uint256, String[200]])
tokenURIs: HashMap[uint256, String[5000]]

# ------------------------------------------------------------------
#                       EXTERNAL FUNCTIONS
# ------------------------------------------------------------------
@deploy
def __init__():
    """
    @notice Contract constructor
    @param sad_svg_uri_ The URI for the sad mood SVG
    @param happy_svg_uri_ The URI for the happy mood SVG
    """

    ow.__init__()
    erc721.__init__(NAME, SYMBOL, JSON_BASE_URI, NAME, EIP_712_VERSION)
    erc721._counter = 0

@external
def mintNFT(
    base64_image: String[2700], 
    subject: String[200], 
    course: String[200]
) -> uint256:
    token_id: uint256 = erc721._counter
    current_token_id: uint256 = token_id
    erc721._counter = token_id + 1
    
    self.image_data[current_token_id] = base64_image
    self.subjects[current_token_id] = subject
    self.courses[current_token_id] = course
    
    erc721._safe_mint(msg.sender, token_id, b"")
    return current_token_id

@external
@view
def tokenURI(token_id: uint256) -> String[FINAL_STRING_SIZE]:
    """
    @notice Get the token URI for a specific token
    @param token_id The ID of the token
    @return The token URI as a base64 encoded JSON string
    """

    assert erc721._exists(token_id), "Token does not exist"
    image_data: String[4000] = self.image_data[token_id]
    subject_data: String[200] = self.subjects[token_id]
    course_data: String[200] = self.courses[token_id]
    # Build the JSON metadata string
    json_string: String[4546] = concat(
    '{"Subject":"',
    subject_data,
    '", "description":"An NFT that certifies the completion of a course", ',
    '"attributes": [{"trait_type": "Course", "value":"',
    course_data,
    '"}], "image":"',
    image_data,
    '"}'
    )
    return concat('data:application/json,', json_string)