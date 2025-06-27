import { createWalletClient, custom, createPublicClient, parseEther, defineChain } from "viem";
import { zksyncSepoliaTestnet } from "viem/chains";
import { abi, contractAddress } from "../utils/constants.js";

let walletClient;
let publicClient;

// Connect to MetaMask wallet
export async function connectWallet() {
    if (typeof window.ethereum !== "undefined") {
        try {
            // Request account access
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            
            walletClient = createWalletClient({
                transport: custom(window.ethereum),
            });
            
            const addresses = await walletClient.getAddresses();
            console.log("Wallet connected successfully!");
            return addresses[0]; // Return the connected address
        } catch (error) {
            console.error("Failed to connect wallet:", error);
            if (error.code === 4001) {
                throw new Error("User rejected the connection request");
            }
            throw new Error("Failed to connect wallet: " + error.message);
        }
    } else {
        throw new Error("Please install MetaMask!");
    }
}

// Get Sepolia chain configuration
async function getCurrentChain() {
    return zksyncSepoliaTestnet; // Use Sepolia testnet
}

// Check if wallet is connected
export async function isWalletConnected() {
    if (typeof window.ethereum !== "undefined") {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            return accounts.length > 0;
        } catch (error) {
            console.error("Error checking wallet connection:", error);
            return false;
        }
    }
    return false;
}

// Get connected account
export async function getConnectedAccount() {
    if (typeof window.ethereum !== "undefined") {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_accounts' });
            return accounts[0] || null;
        } catch (error) {
            console.error("Error getting connected account:", error);
            return null;
        }
    }
    return null;
}

// Mint certificate function
export async function mintCertificate(userDetails) {
    if (typeof window.ethereum !== "undefined") {
        try {
            // Ensure wallet is connected
            const connectedAccount = await getConnectedAccount();
            if (!connectedAccount) {
                throw new Error("No wallet connected");
            }

            // Initialize wallet client if not already done
            if (!walletClient) {
                walletClient = createWalletClient({
                    transport: custom(window.ethereum),
                });
            }

            const currentChain = await getCurrentChain();

            // Initialize public client
            publicClient = createPublicClient({
                transport: custom(window.ethereum),
                chain: currentChain,
            });

            // Simulate the contract call first
            const { request } = await publicClient.simulateContract({
                address: contractAddress,
                abi: abi,
                functionName: "mintCertificate",
                account: connectedAccount,
                args: [userDetails.name, userDetails.subject, userDetails.completionDate],
            });

            console.log("Simulation request:", request);

            // Execute the transaction
            const hash = await walletClient.writeContract(request);
            console.log("Certificate minting transaction hash:", hash);

            return {
                success: true,
                transactionHash: hash,
                account: connectedAccount
            };

        } catch (error) {
            console.error("Failed to mint certificate:", error);
            throw new Error(`Failed to mint certificate: ${error.message}`);
        }
    } else {
        throw new Error("Please install MetaMask!");
    }
}

// Mint NFT certificate function
export async function mintNFTContract(imageData, subject, course) {
    if (typeof window.ethereum !== "undefined") {
        try {
            // Ensure wallet is connected
            const connectedAccount = await getConnectedAccount();
            if (!connectedAccount) {
                throw new Error("No wallet connected");
            }

            const currentChain = await getCurrentChain();

            // Initialize wallet client with chain
            if (!walletClient) {
                walletClient = createWalletClient({
                    transport: custom(window.ethereum),
                    chain: currentChain,
                });
            }

            // Initialize public client with chain
            publicClient = createPublicClient({
                transport: custom(window.ethereum),
                chain: currentChain,
            });

            // Simulate the contract call first
            const { request } = await publicClient.simulateContract({
                address: contractAddress,
                abi: abi,
                functionName: "mintNFT",
                account: connectedAccount,
                chain: currentChain,
                args: [imageData, subject, course],
            });

            console.log("Simulation request:", request);

            // Execute the transaction with chain parameter
            const hash = await walletClient.writeContract({
                ...request,
                chain: currentChain,
            });
            console.log("NFT minting transaction hash:", hash);

            return {
                success: true,
                transactionHash: hash,
                account: connectedAccount
            };

        } catch (error) {
            console.error("Failed to mint NFT:", error);
            throw new Error(`Failed to mint NFT: ${error.message}`);
        }
    } else {
        throw new Error("Please install MetaMask!");
    }
}
    