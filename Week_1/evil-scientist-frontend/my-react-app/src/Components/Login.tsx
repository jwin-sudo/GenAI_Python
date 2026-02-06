import { useEffect, useRef, useState } from "react"
import { Button, Container, Form } from "react-bootstrap"
import { useNavigate } from "react-router-dom"

export const Login: React.FC = () => {

    // Set up state for username and password 
    const [username, setUsername] = useState<string>("")
    const [password, setPassword] = useState<string>("")
    // define my useNavigate hook so we can switch URLs programmatically

    const navigate = useNavigate()

    // Use the useRef and useEffect hooks to "focus" our username input box on component load 
    const usernameRef = useRef<HTMLInputElement>(null)

    useEffect(() => {
        usernameRef.current?.focus() // "focus" whatever the ref is pointing to, so the user can type right away 
        
    })


    const login = () => {

        // hardcoded - this would be an HTTP request 

        if (username == "evilguy" && password == "password"){
            navigate("/dashboard")
        } else {
            alert("Incorrect credentials!")
        }
    }

    return (
        // Bootstreap gives us this Container element - it does some default padding/centering
        <Container>
            <h1>Evil Scientist Corp. Login</h1>

            <div>
                <Form.Control 
                    type = "text"
                    placeholder = "username"
                    name = "username"
                    ref={usernameRef}
                />
            </div>

            <div>
                <Form.Control
                    type="password"
                    placeholder="password"
                    name="password"
                />
            </div>

            <Button className="btn-success m-1">Login</Button>
        </Container>
    )
}