import base64
from src import mint_certificate2
from moccasin.config import get_active_network

# Here we used manifest_named to check if the contract is already deployed by looking into the db

# Replace this with your deployed contract address
DEPLOYED_CONTRACT_ADDRESS = "0x5497D3d6aE886f709a7427B1f7f8DE0A2c715bCC"

def mint():
    certificate_svg_uri = ""
    with open("./images/certificate4.svg", "r") as f:
        certificate_svg = f.read()
        certificate_svg_uri = svg_to_base64_uri(certificate_svg)
    # STUDENT_NAME = "John Doe"
    # PROVIDER_NAME = "University of Example"
    SUBJECT = "Computer Science"
    COURSE_NAME = "Blockchain Development"
    TO_ADDRESS = "0x25600B6A2faC246e1807600Df51D632D9eae52fe"

    print(certificate_svg_uri)
    active_network = get_active_network()
    print(f"Active network: {active_network.name}")
    nft_certificate = mint_certificate2.at(DEPLOYED_CONTRACT_ADDRESS)
    print(f"Minting NFT from contract at {nft_certificate.address} on network {active_network.name}")
    nft_certificate.mintNFT(certificate_svg_uri , SUBJECT, COURSE_NAME)
    print(nft_certificate.tokenURI(0))

def moccasin_main():
    return mint()


def svg_to_base64_uri(svg):
    """
    Convert SVG content to a base64 encoded string.
    """
    svg_bytes = svg.encode('utf-8')
    base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{base64_svg}"