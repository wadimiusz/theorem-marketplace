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

    // Extract the theorem from the page (we'll need to pass it to the contract)
    const theorem = "{{ bounty.theorem|tojson }}";  // Pass the theorem from Flask to JavaScript

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

        try {
            // Request account access if needed
            await window.ethereum.request({ method: 'eth_requestAccounts' });

            // Instantiate provider and signer
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();

            // Instantiate the contract
            const contract = new ethers.Contract(contractAddress, contractABI, signer);

            // Send the transaction
            console.log("Theorem:", theorem);
            console.log("Proof:", proof);
            const tx = await contract.requestBounty(theorem, proof);
            
            statusMessage.textContent = 'Transaction submitted. Waiting for confirmation...';

            // Wait for transaction to be mined
            const receipt = await tx.wait();

            if (receipt.status === 1) {
                statusMessage.textContent = 'Proof submitted successfully!';
                // Optionally, clear the form or perform other actions
                submitProofForm.reset();
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
