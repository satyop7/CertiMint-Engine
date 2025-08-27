# Contract address: 0x5497D3d6aE886f709a7427B1f7f8DE0A2c715bCC
from src import mint_certificate2



def deploy_certificate():

    certificate_contract = mint_certificate2.deploy() 
    print(f"Contract address is: {certificate_contract.address}")

def moccasin_main():
    deploy_certificate()


