/* This is a basic implementation of a global store, basically globally accessible data

    Any data you want to use throughout the app can reside here 
    Look into Context API for the best practice way of doing this 

*/

export const store = {
    //Imagine this gets populated when a user logs in. 
    // Great way to personalize the app with that particular user's data
    loggedInUser: {
        id:0,
        username: "",
        email:""
    }
}

/*THIS ISN'T BEST PRACTICE FOR GLOBAL DATA 

- The data will be wiped if you refresh the page 
- This data has nothing to do with state, it's not REACTive 
- This is not very secure either. No encapsulation

- Context API would fix all three of these issues! :)

*/
