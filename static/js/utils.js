export const SEPOLIA_CHAIN_ID_HEX = '0xaa36a7'; // 11155111 in hex format

// Ensures that the user's wallet is connected to the Sepolia network.
// If the wallet is on another network, the function requests a network switch.
// If Sepolia is not added to the wallet, it attempts to add it first.
export async function ensureSepoliaNetwork() {
    if (!window.ethereum) {
        throw new Error('No Ethereum provider found. Please install MetaMask.');
    }

    const currentChainId = await window.ethereum.request({ method: 'eth_chainId' });

    if (currentChainId === SEPOLIA_CHAIN_ID_HEX) {
        // Already on Sepolia – nothing to do.
        return;
    }

    try {
        // Try switching to Sepolia if it is already added in the wallet.
        await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: SEPOLIA_CHAIN_ID_HEX }],
        });
    } catch (switchError) {
        // 4902 error code means the chain has not been added to MetaMask.
        if (switchError.code === 4902) {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [
                    {
                        chainId: SEPOLIA_CHAIN_ID_HEX,
                        chainName: 'Sepolia',
                        rpcUrls: ['https://rpc.sepolia.org'],
                        nativeCurrency: {
                            name: 'Sepolia Ether',
                            symbol: 'SEP',
                            decimals: 18,
                        },
                        blockExplorerUrls: ['https://sepolia.etherscan.io'],
                    },
                ],
            });
        } else {
            // Re-throw other errors so calling code can handle (or surface) them.
            throw switchError;
        }
    }
} 