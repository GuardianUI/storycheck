// examples/simple-web3-app/src/App.jsx
import { useState, useEffect } from 'react'
import { useAccount, useConnect, useSendTransaction, useChainId, useChains, useSwitchChain } from 'wagmi'
import { parseEther } from 'viem'
import { usePublicClient } from 'wagmi'
import { normalize } from 'viem/ens'
import { mainnet } from 'viem/chains'

export default function App() {
  const { isConnected } = useAccount()
  const { connect, connectors } = useConnect()
  const { address } = useAccount()
  const { sendTransaction, isLoading, error } = useSendTransaction()
  const chainId = useChainId()
  const chains = useChains()
  const { switchChain } = useSwitchChain()
  const currentChain = chains.find(c => c.id === chainId) || mainnet
  const explorerSlugs = {
    1: 'eth', // Mainnet
    11155111: 'sepolia', // Sepolia
    // Add more chains as needed
  }
  const chainSlug = explorerSlugs[chainId] || 'eth' // Default to eth

  const [to, setTo] = useState('')
  const [amount, setAmount] = useState('')
  const client = usePublicClient({ chainId: mainnet.id })
  const [successHash, setSuccessHash] = useState(null)
  const [rejectionError, setRejectionError] = useState(null)
  const [hasInitialSwitch, setHasInitialSwitch] = useState(false)

  const handleSend = async () => {
    if (to && amount) {
      let resolvedTo = to;
      if (to.endsWith('.eth')) {
        try {
          resolvedTo = await client.getEnsAddress({ name: normalize(to) });
          if (!resolvedTo) {
            throw new Error(`ENS name ${to} could not be resolved`);
          }
        } catch (err) {
          console.error('ENS resolution failed:', err.message);
          return;
        }
      }
      sendTransaction({
        to: resolvedTo,
        value: parseEther(amount),
        chainId,
        account: address,
      },
      {
        onSuccess: (data) => {
          setSuccessHash(data.hash)
        },
        onError: (err) => {
          if (err.name === 'UserRejectedRequestError') {
            setRejectionError('Transaction rejected in wallet.')
          } else {
            setRejectionError(`Transaction error: ${err.message}`)
          }
        },
      }
      )
      console.log('Transaction sent:', { to: resolvedTo, amount, address })
    }
    if (error) console.error('Transaction failed:', error.message)
  }

  useEffect(() => {
    if (isConnected && !hasInitialSwitch && chainId !== mainnet.id) {
      setHasInitialSwitch(true)
      switchChain({ chainId: mainnet.id })
    }
  }, [isConnected, hasInitialSwitch, chainId, switchChain])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg shadow-lg text-center">
        <h1 className="text-2xl font-bold mb-4">Simple Web3 App</h1>
        {!isConnected ? (
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded"
            onClick={() => connect({ connector: connectors[0] })}
          >
            {isLoading ? 'Connecting...' : 'Connect Wallet'}
          </button>
        ) : (
          <div>
            <input
              type="text"
              placeholder="ENS name or address (e.g., vitalik.eth)"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="border p-2 mb-2 w-full"
            />
            <input
              type="number"
              placeholder="ETH amount (e.g., 0.01)"
              value={amount}
              step="any"
              onChange={(e) => setAmount(e.target.value)}
              className="border p-2 mb-2 w-full"
            />
            <button
              className="bg-green-500 text-white px-4 py-2 rounded"
              onClick={handleSend}
            >
              {isLoading ? 'Sending...' : 'Send ETH'}
              {error && <div className="text-red-500">{error.message}</div>}
            </button>
            <div className="mt-4">
              Current Network: {currentChain.name}
              <select
                value={chainId}
                onChange={(e) => switchChain({ chainId: Number(e.target.value) })}
                className="ml-2 border p-1"
              >
                {chains.map((chain) => (
                  <option key={chain.id} value={chain.id}>{chain.name}</option>
                ))}
              </select>
            </div>
            {successHash && (
              <div className="mt-2 text-green-500">
                Transaction successful! View on <a href={`https://www.oklink.com/${chainSlug}/tx/${successHash}`} target="_blank" rel="noopener noreferrer" className="underline">OKLink</a>
              </div>
            )}
            {rejectionError && (
              <div className="mt-2 text-red-500">
                {rejectionError}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}