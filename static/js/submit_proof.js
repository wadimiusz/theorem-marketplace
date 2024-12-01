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
    const submitProofForm = document.getElementById('submitProofForm');
    const statusMessage = document.getElementById('statusMessage');

    // Add event listener to the form submission
    submitProofForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Get the proof from the form
        const proof = document.getElementById('proof').value;

        // Validate input
        if (!proof) {
            statusMessage.textContent = 'Please enter your proof.';
            return;
        }
// Disable the submit button to prevent multiple submissions
    submitProofForm.querySelector('button[type="submit"]').disabled = true;

    // **Add Syntax Checking Step**
    statusMessage.textContent = 'Checking proof syntax... Please wait.';

    try {
        const syntaxCheckResponse = await fetch('/api/check_syntax', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: proof })
        });
        const syntaxCheckResult = await syntaxCheckResponse.json();

        if (!syntaxCheckResult.success) {
            statusMessage.textContent = `Syntax Error: ${syntaxCheckResult.error}`;
            submitProofForm.querySelector('button[type="submit"]').disabled = false;
            return;
        }
    } catch (error) {
        console.error('Syntax checking error:', error);
        statusMessage.textContent = 'An error occurred during syntax checking.';
        submitProofForm.querySelector('button[type="submit"]').disabled = false;
        return;
    }

    // Proceed with transaction as before
    statusMessage.textContent = 'Syntax check passed. Sending transaction...';

        try {
    // Request account access if needed
    await window.ethereum.request({ method: 'eth_requestAccounts' });

    // Instantiate provider and signer
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const signer = provider.getSigner();

    // Instantiate the contract
    const contract = new ethers.Contract(contractAddress, contractABI, signer);

    // Send the transaction
    const tx = await contract.requestBounty(theorem, proof);
    const txHash = tx.hash;

    const etherscanBaseUrl = 'https://sepolia.etherscan.io/tx/';
    const etherscanLink = `${etherscanBaseUrl}${txHash}`;
    statusMessage.innerHTML = `Transaction submitted. <a href="${etherscanLink}" target="_blank">View on Etherscan</a>. Waiting for confirmation...`;

    // Wait for transaction to be mined
    const receipt = await tx.wait();

    // Check if the transaction was successful
    if (receipt.status === 1) {
        statusMessage.innerHTML = `Proof submitted successfully! <a href="${etherscanLink}" target="_blank">View on Etherscan</a>.`;
        // Optionally, clear the form or perform other actions
        submitProofForm.reset();
    } else {
        statusMessage.textContent = 'Transaction failed.';
    }
} catch (error) {
    console.error('Error:', error);

    if (error.code === ethers.errors.TRANSACTION_REPLACED) {
        if (error.cancelled) {
            statusMessage.textContent = 'Transaction was cancelled.';
        } else {
            // Transaction was replaced by a new one
            // You can check if the replacement transaction was successful
            const replacementReceipt = error.receipt;
            const replacementTxHash = error.replacement.hash;
            const etherscanReplacementLink = `${etherscanBaseUrl}${replacementTxHash}`;

            if (replacementReceipt && replacementReceipt.status === 1) {
                statusMessage.innerHTML = `Proof submitted successfully! (Transaction replaced) <a href="${etherscanReplacementLink}" target="_blank">View on Etherscan</a>`;
                console.log('Replacement transaction hash:', replacementReceipt.transactionHash);
                // Optionally, clear the form or perform other actions
                submitProofForm.reset();

                // If needed, store the replacement transaction hash
                const replacementTxHash = replacementReceipt.transactionHash;
                // ... use replacementTxHash as needed ...
            } else {
                statusMessage.textContent = 'Replacement transaction failed.';
            }
        }
    } else if (error.code === 4001) {
        // User rejected transaction
        statusMessage.textContent = 'Transaction rejected by user.';
    } else {
        statusMessage.textContent = 'An error occurred. See console for details.';
    }
}
    });
});
