import axios from "axios"
import { useState } from "react"
import { Button, Card, Form } from "react-bootstrap"

export const Chat:React.FC = () => {
    
    // Set up some state to capture LLM input and output
    const [input, setInput] = useState<string>("")
    const [output, setOutput] = useState<string>("")
    // One more state object to track whether the LLM response is loading 
    const [loading, setLoading] = useState<boolean>(false)

    // Function that sends the chat and captures the response 

    // Function that sends the chat and captures the response
    const sendMessage = async () => {

        //set loading to true as the LLM response load 
        setLoading(true)
        const response = await axios.post("http://127.0.0.1:8000/chat/memory-chat", {input:input})

        //print out the response just to see it 
        console.log(response)

        //set the response in state, wipe the input state 
        setOutput(response.data.response)
        /* response.data.response?? wut

           response 1 is the actual HTTP response
           data is the data within the HTTP response
           response 2 is the field in data called "response" 
        */

        setInput("")
        setLoading(false)

        //temporary, to delete 
        alert(output) 
    }

    return(
        <Card>
            <h4>Evil Scientist Chat</h4>

            <Form.Control
            type="text"
            placeholder="Send a message to your virtual assistant..."
            value = {input} // We need this for onChange
            //Whenever this input CHANGES, save the value in state 

            onChange = {(event) => setInput(event.target.value)}
            className="mb-2"
            />

            {/* TERNARY OPERATOR FOR CONDITIONAL RENDERING */}
            <Button onClick={sendMessage} disabled={loading}>
                {loading ? "Thinking..." : "Send Message"}
                {/* In English: if loading == true, the button 
                say s "Thinking..." */}
            </Button>

            {/* Another style of conditional rendering - If 
            there is a value for output, render it on the page. Otherwise render nothing */}

            {output && (
                <Card>
                    <h4>Response: </h4>

                    <p>{output}</p>

                </Card>
            )}
            
        </Card>
    )

}