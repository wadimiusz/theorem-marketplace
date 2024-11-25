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
