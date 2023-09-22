let token = localStorage.getItem("access_token");
if (token) {
  // 如果有 token 代表使用者曾經登入過
  // 接下來驗證 token 是否有效
  verifyToken();
} else {
  console.log("尚未登入過");
}
// 驗證 Token
async function verifyToken() {
  const signIn = document.querySelector("#signIn");
  const signOut = document.querySelector("#signOut");
  try {
    const response = await fetch("/api/verifyToken", {
      methods: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Token 無效，請重新登入");
    }
    // 處理 API 回傳的資料
    const data = await response.json();
    signIn.style.display = "none";
    signOut.style.display = "block";
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
      account: signUpAccount,
      password: signUpPassword,
    };

    try {
      // 發送 POST 請求到 /api/signup
      const response = await fetch("/api/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // 註冊成功 (200)
      const data = await response.json();
      if (!response.ok) {
        signUpMsg.style.display = "block";
        signUpMsg.textContent = data.message;
      } else {
        signUpMsg.style.display = "block";
        signUpMsg.textContent = data.message;
      }
    } catch (error) {
      console.error("註冊失敗:", error);
    }
  }
});

// 登入
signInButton.addEventListener("click", async function () {
  console.log('test')
  event.preventDefault();
  const signInAccount = signInForm.elements.signInAccount.value;
  const signInPassword = signInForm.elements.signInPassword.value;
  const signInMsg = document.querySelector(".signInMsg");

  // 檢查註冊表單填寫，任一空值阻擋行為
  if (signInAccount == "" || signInPassword == "") {
    signInMsg.style.display = "block";
    signInMsg.textContent = "電子信箱及密碼不可為空";
  } else {
    const userData = {
      account: signInAccount,
      password: signInPassword,
    };

    try {
      const response = await fetch("/api/signin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      // 登入成功
      const data = await response.json();
      if (response.ok) {
        console.log("登入成功");
        signInMsg.style.display = "block";
        signInMsg.textContent = data.message;
        localStorage.setItem("access_token", data.access_token);
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