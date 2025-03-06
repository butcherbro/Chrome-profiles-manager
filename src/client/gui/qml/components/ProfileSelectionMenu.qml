import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 20

        // Заголовок
        Text {
            text: "Способ выбора профилей"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Кнопки выбора
        Column {
            Layout.fillWidth: true
            spacing: 15

            // Кнопка "Выбрать из списка"
            Button {
                width: parent.width
                height: 50
                flat: true

                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }

                contentItem: RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 15
                    
                    Text {
                        text: "📋"
                        font.pixelSize: 24
                        Layout.preferredWidth: 30
                    }
                    
                    Text {
                        text: "Выбрать из списка"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                onClicked: {
                    var stackView = findStackView(root)
                    if (stackView) stackView.push(profileListSelection)
                }
            }

            // Кнопка "Ввести имена"
            Button {
                width: parent.width
                height: 50
                flat: true

                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }

                contentItem: RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 15
                    
                    Text {
                        text: "✏️"
                        font.pixelSize: 24
                        Layout.preferredWidth: 30
                    }
                    
                    Text {
                        text: "Ввести имена"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                onClicked: {
                    var stackView = findStackView(root)
                    if (stackView) stackView.push(profileNameEntry)
                }
            }

            // Кнопка "Выбрать по комментарию"
            Button {
                width: parent.width
                height: 50
                flat: true

                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }

                contentItem: RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    anchors.rightMargin: 15
                    spacing: 15
                    
                    Text {
                        text: "🔍"
                        font.pixelSize: 24
                        Layout.preferredWidth: 30
                    }
                    
                    Text {
                        text: "Выбрать по комментарию"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                onClicked: {
                    var stackView = findStackView(root)
                    if (stackView) stackView.push(profileCommentSelection)
                }
            }
        }

        // Растягивающийся элемент
        Item {
            Layout.fillHeight: true
        }

        // Кнопка "Назад"
        Button {
            text: "Назад"
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            Layout.bottomMargin: 10
            flat: true

            background: Rectangle {
                color: parent.hovered ? "#e0e0e0" : "#ffffff"
                border.color: "#d0d0d0"
                radius: 2
            }

            contentItem: Text {
                text: parent.text
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 14
            }

            onClicked: root.backClicked()
        }
    }
    
    // Функция для поиска StackView
    function findStackView(item) {
        if (item.parent) {
            if (item.parent instanceof StackView) {
                return item.parent
            } else {
                return findStackView(item.parent)
            }
        }
        return null
    }
} 