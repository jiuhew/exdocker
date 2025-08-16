import { useEffect, useState } from 'react'

export default function App() {
	const [health, setHealth] = useState<string>('loading...')
	const [taskId, setTaskId] = useState<string>('')

	useEffect(() => {
		fetch('/api/health/')
			.then((r) => r.json())
			.then((d) => setHealth(JSON.stringify(d)))
			.catch((e) => setHealth('error: ' + e.message))
	}, [])

	const triggerTask = async () => {
		const res = await fetch('/api/common/add/?x=1&y=2')
		const json = await res.json()
		setTaskId(json.task_id || 'error')
	}

	return (
		<div style={{ padding: 24, fontFamily: 'system-ui' }}>
			<h2>React + Django + Celery + Redis + MySQL</h2>
			<p>Health: {health}</p>
			<button onClick={triggerTask}>Trigger Celery add(1,2)</button>
			{taskId && <p>Task queued: {taskId}</p>}
		</div>
	)
}


