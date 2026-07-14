import tkinter


def main():
    print("hi")
    window = tkinter.Tk()
    canvas = tkinter.Canvas(window, width=800, height=600)
    canvas.pack()
    canvas.create_rectangle(10, 20, 400, 300)
    canvas.create_oval(100, 100, 150, 150)
    canvas.create_text(200, 150, text="Hi!")
    tkinter.mainloop()


if __name__ == "__main__":
    main()
