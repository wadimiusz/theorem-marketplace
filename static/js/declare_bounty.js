const contractABI = [
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "BountyDeclared",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "bytes32",
				"name": "requestID",
				"type": "bytes32"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "BountyPaid",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "bytes32",
				"name": "requestID",
				"type": "bytes32"
			},
			{
				"indexed": false,
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			}
		],
		"name": "BountyRequestDeclined",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			}
		],
		"name": "BountyRequested",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "bytes32",
				"name": "id",
				"type": "bytes32"
			}
		],
		"name": "ChainlinkCancelled",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "bytes32",
				"name": "id",
				"type": "bytes32"
			}
		],
		"name": "ChainlinkFulfilled",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "bytes32",
				"name": "id",
				"type": "bytes32"
			}
		],
		"name": "ChainlinkRequested",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "from",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "to",
				"type": "address"
			}
		],
		"name": "OwnershipTransferRequested",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "from",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "to",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "acceptOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			}
		],
		"name": "declareBounty",
		"outputs": [],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "_requestId",
				"type": "bytes32"
			},
			{
				"internalType": "bool",
				"name": "_success",
				"type": "bool"
			}
		],
		"name": "fulfill",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "proof",
				"type": "string"
			}
		],
		"name": "requestBounty",
		"outputs": [
			{
				"internalType": "bytes32",
				"name": "requestId",
				"type": "bytes32"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "to",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "withdrawLink",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_oracle",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "_jobId",
				"type": "string"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "bytes32",
				"name": "",
				"type": "bytes32"
			}
		],
		"name": "requests",
		"outputs": [
			{
				"internalType": "address payable",
				"name": "sender",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "theorem",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "theoremBounties",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]
const contractAddress = '0xc671A4a18DA81D6Df1A9C3619045D10FaCFB3936'

// Ensure the DOM is loaded
window.addEventListener('DOMContentLoaded', async () => {
    // Check if MetaMask is installed
    if (typeof window.ethereum !== 'undefined') {
        console.log('MetaMask is installed!');
    } else {
        alert('Please install MetaMask to use this feature.');
        return;
    }

    // Get references to form elements
    const declareBountyForm = document.getElementById('declareBountyForm');
    const statusMessage = document.getElementById('statusMessage');

    // Add event listener to the form submission
    declareBountyForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Get form values
        const theorem = document.getElementById('theorem').value;
        const bountyAmount = document.getElementById('bounty_amount').value;

        // Validate inputs
        if (!theorem || !bountyAmount) {
            statusMessage.textContent = 'Please fill out all fields.';
            return;
        }

        // Convert bounty amount to Wei (smallest unit of Ether)
        const bountyAmountWei = ethers.utils.parseEther(bountyAmount);

        try {
            // Request account access if needed
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            // Instantiate the contract
            const contract = new ethers.Contract(contractAddress, contractABI, signer);

            // Send the transaction
            const tx = await contract.declareBounty(theorem, {
                value: bountyAmountWei
            });

            statusMessage.textContent = 'Transaction submitted. Waiting for confirmation...';

            // Wait for transaction to be mined
            const receipt = await tx.wait();

if (receipt.status === 1) {
    statusMessage.textContent = 'Bounty declared successfully!';

    // Prepare data to send to the backend
    const data = {
        theorem: theorem,
        bounty_amount: bountyAmount,
        transaction_hash: receipt.transactionHash,
        user_address: await signer.getAddress()
    };

    // Send the data to the backend
    fetch('/api/add_bounty', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            console.log('Bounty added to the database.');
            // Optionally, redirect to the bounties list
            // window.location.href = '/bounties';
        } else {
            statusMessage.textContent = 'Failed to add bounty to the database.';
            console.error('Server responded with status:', response.status);
        }
    })
    .catch(error => {
        statusMessage.textContent = 'An error occurred while updating the database.';
        console.error('Error:', error);
    });
} else {
    statusMessage.textContent = 'Transaction failed.';
}

        } catch (error) {
            console.error('Error:', error);
            if (error.code === 4001) {
                // User rejected transaction
                statusMessage.textContent = 'Transaction rejected by user.';
            } else {
                statusMessage.textContent = 'An error occurred. See console for details.';
            }
        }
    });
});
