let token = localStorage.getItem("access_token");
let userData = {};
document.addEventListener("DOMContentLoaded", async function () {
  if (token) {
    // 如果有 token 代表使用者曾經登入過
    // 接下來驗證 token 是否有效
    let isLogin = await verifyToken();
    if (isLogin) {
      console.log("登入成功");
      const signIn = document.querySelector("#signIn");
      const signOut = document.querySelector("#signOut");
      signOut.style.display = "block";
      signIn.style.display = "none";
      // 開啟預定行程購物車 /booking 頁面
      const goToBooking = document.getElementById("goToBooking");
      goToBooking.addEventListener("click", async function () {
        window.location.href = "/booking";
        await getOrderData();
      });
    } else {
      console.log("Token 無效，請重新登入");
      localStorage.removeItem("access_token");
    }
  } else {
    console.log("尚未登入過");
    goToBooking.addEventListener("click", function () {
      signInBox.style.display = "flex";
    });
  }
});

// 驗證 Token
async function verifyToken() {
  try {
    if (token) {
      const response = await fetch("/api/user/auth", {
        methods: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.log("Token 無效，請重新登入");
        localStorage.removeItem("access_token");
        return false;
      }
      // 處理 API 回傳的資料
      const data = await response.json();
      userData = data.data;
      // console.log(userData);
      return true;
    } else {
      console.log("尚未登入過");
    }
  } catch (error) {
    console.error("發生錯誤：", error);
  }
}

// 登入 & 註冊畫面
const clickSignIn = document.querySelector("#signIn");
const goToSignUp = document.querySelector(".goToSignUp");
const goToSignIn = document.querySelector(".goToSignIn");
const signInBox = document.querySelector(".signInBoxContainer");
const signUpBox = document.querySelector(".signUpBoxContainer");
const closeSignInBox = document.querySelector("#closeSignIn");
const closeSignUpBox = document.querySelector("#closeSignUp");

// 開啟登入畫面
clickSignIn.addEventListener("click", function () {
  signInBox.style.display = "flex";
});

goToSignIn.addEventListener("click", function () {
  signUpBox.style.display = "none";
  signInBox.style.display = "flex";
});

// 開啟註冊畫面
goToSignUp.addEventListener("click", function () {
  signInBox.style.display = "none";
  signUpBox.style.display = "flex";
});

// 關閉登入畫面
closeSignInBox.addEventListener("click", function () {
  signInBox.style.display = "none";
});

closeSignUpBox.addEventListener("click", function () {
  signUpBox.style.display = "none";
});

// Sign Up Btn & Sign In Btn & Sign Out 監聽事件
const signUpForm = document.getElementById("signUpForm");
const signUpButton = document.getElementById("signUpButton");
const signInForm = document.getElementById("signInForm");
const signInButton = document.getElementById("signInButton");
const signOut = document.querySelector("#signOut");

// 註冊
signUpButton.addEventListener("click", async function () {
  event.preventDefault();
  const signUpName = signUpForm.elements.signUpName.value;
  const signUpAccount = signUpForm.elements.signUpAccount.value;
  const signUpPassword = signUpForm.elements.signUpPassword.value;
  const signUpMsg = document.querySelector(".signUpMsg");
  const goToSignIn = document.querySelector(".goToSignIn");

  // 檢查註冊表單填寫，任一空值阻擋行為
  if (signUpName == "" || signUpAccount == "" || signUpPassword == "") {
    signUpMsg.style.display = "block";
    signUpMsg.textContent = "以上欄位皆為必填，請填寫完成後再送出";
  } else {
    const userData = {
      name: signUpName,
      email: signUpAccount,
      password: signUpPassword,
    };

    try {
      // 發送 POST 請求到 /api/user
      const response = await fetch("/api/user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // 註冊成功 (200)
      const data = await response.json();
      if (!data.ok) {
        signUpMsg.style.display = "block";
        signUpMsg.textContent = data.message;
      } else {
        signUpMsg.style.display = "block";
        signUpMsg.textContent = "註冊成功，請重新登入";
      }
    } catch (error) {
      console.error("註冊失敗:", error);
    }
  }
});

// 登入
signInButton.addEventListener("click", async function () {
  event.preventDefault();
  const signInAccount = signInForm.elements.signInAccount.value;
  const signInPassword = signInForm.elements.signInPassword.value;
  const signInMsg = document.querySelector(".signInMsg");

  // 檢查登入表單填寫，任一空值阻擋行為
  if (signInAccount == "" || signInPassword == "") {
    signInMsg.style.display = "block";
    signInMsg.textContent = "電子信箱及密碼不可為空";
  } else {
    const userData = {
      email: signInAccount,
      password: signInPassword,
    };

    try {
      const response = await fetch("/api/user/auth", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // 登入成功
      const data = await response.json();
      if (response.ok) {
        signInMsg.style.display = "block";
        signInMsg.textContent = "登入成功！網頁重新加載中...";
        localStorage.setItem("access_token", data.token);
        setTimeout(function () {
          window.location.reload();
        }, 2000);
      } else {
        signInMsg.style.display = "block";
        signInMsg.textContent = data.message;
      }
    } catch (error) {
      console.error("登入失敗:", error);
    }
  }
});

// 登出
signOut.addEventListener("click", function () {
  event.preventDefault();
  // 刪除 token
  localStorage.removeItem("access_token");
  alert("已登出，期待再見～");
  setTimeout(function () {
    window.location.reload();
  }, 1000);
});
