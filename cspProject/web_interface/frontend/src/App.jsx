import { useState } from 'react'
import axios from 'axios'
import './index.css'

function App() {
    const [schedule, setSchedule] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // Filters
    const [selectedSection, setSelectedSection] = useState('')
    const [selectedInstructor, setSelectedInstructor] = useState('')

    const fetchSchedule = async () => {
        setLoading(true)
        setError(null)
        try {
            // Use helper if in dev mode to point to port 5000, or rely on proxy
            const response = await axios.get('/api/solve')
            if (response.data.status === 'success') {
                setSchedule(response.data.data)
            } else {
                setError(response.data.message || 'Failed to generate schedule')
            }
        } catch (err) {
            console.error(err)
            setError(err.response?.data?.error || 'Server error occurred. Is the backend running?')
        } finally {
            setLoading(false)
        }
    }

    // Get unique values for filters
    const uniqueSections = [...new Set(schedule.flatMap(item => item.sections))].sort()
    const uniqueInstructors = [...new Set(schedule.map(item => item.instructor))].sort()

    // Filter logic
    const filteredSchedule = schedule.filter(item => {
        const sectionMatch = selectedSection ? item.sections.includes(selectedSection) : true
        const instructorMatch = selectedInstructor ? item.instructor === selectedInstructor : true
        return sectionMatch && instructorMatch
    })

    // Group by TimeSlot (rows)
    const timeSlots = [
        "9:00 AM - 10:30 AM",
        "10:45 AM - 12:15 PM",
        "12:30 PM - 2:00 PM",
        "2:15 PM - 3:45 PM"
    ]

    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]

    return (
        <div className="app-container">
            <header className="header">
                <div className="header-content">
                    <h1>📅 University Scheduler</h1>
                    <p>AI-Powered CSP Timetable Generator</p>
                </div>
                <button
                    className="generate-btn"
                    onClick={fetchSchedule}
                    disabled={loading}
                >
                    {loading ? 'Generating...' : '✨ Generate Timetable'}
                </button>
            </header>

            {error && (
                <div className="error-banner">
                    ⚠️ {error}
                </div>
            )}

            {schedule.length > 0 && (
                <main className="main-content">
                    <div className="controls">
                        <div className="control-group">
                            <label>Filter by Section</label>
                            <select
                                value={selectedSection}
                                onChange={(e) => setSelectedSection(e.target.value)}
                            >
                                <option value="">All Sections</option>
                                {uniqueSections.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>

                        <div className="control-group">
                            <label>Filter by Instructor</label>
                            <select
                                value={selectedInstructor}
                                onChange={(e) => setSelectedInstructor(e.target.value)}
                            >
                                <option value="">All Instructors</option>
                                {uniqueInstructors.map(i => <option key={i} value={i}>{i}</option>)}
                            </select>
                        </div>

                        <button
                            className="reset-btn"
                            onClick={() => { setSelectedSection(''); setSelectedInstructor('') }}
                        >
                            Reset Filters
                        </button>
                    </div>

                    <div className="timetable-container">
                        <div className="grid-header">
                            <div className="grid-cell corner">Time / Day</div>
                            {days.map(day => (
                                <div key={day} className="grid-cell day-header">{day}</div>
                            ))}
                        </div>

                        {timeSlots.map(slot => (
                            <div key={slot} className="grid-row">
                                <div className="grid-cell time-header">{slot}</div>
                                {days.map(day => {
                                    // Find items for this slot and day
                                    const items = filteredSchedule.filter(
                                        item => item.day === day && (item.startTime + " - " + item.endTime) === slot
                                    )

                                    return (
                                        <div key={day + slot} className="grid-cell content-cell">
                                            {items.map(item => (
                                                <div key={item.id} className={`card ${item.colorType}`}>
                                                    <div className="card-header">
                                                        <span className="course-code">{item.course}</span>
                                                        <span className="type-badge">{item.type}</span>
                                                    </div>
                                                    <div className="card-body">
                                                        <div className="sections">
                                                            {item.sections.map(s => <span key={s} className="pill">{s}</span>)}
                                                        </div>
                                                        <div className="instructor">
                                                            👨‍🏫 {item.instructor}
                                                        </div>
                                                        <div className="room">
                                                            📍 {item.room}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )
                                })}
                            </div>
                        ))}
                    </div>
                </main>
            )}

            {schedule.length === 0 && !loading && !error && (
                <div className="empty-state">
                    <h2>Ready to Schedule</h2>
                    <p>Click the generate button to start the AI solver.</p>
                </div>
            )}
        </div>
    )
}

export default App
